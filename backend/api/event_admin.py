from datetime import timedelta
from uuid import UUID
from django.core import signing
from django.contrib.auth import get_user_model
from django.http import Http404
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import Event, EventAdministrator
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPreference, ParticipantPhoto
from apps.moderation.models import EventSuspension, EventBan, ModerationCase, ModerationAction, ModerationNote, UserSuspension
from apps.reports.models import Report, Block, ReportEvidence
from apps.matches.models import Match
from apps.messaging.models import Conversation
from apps.audit.models import AuditLog
from apps.notifications.models import Notification
from apps.notifications.announcements import deliver_sent_announcements
from .services import DEFAULT_FILTERS, age
from types import SimpleNamespace
from apps.events.permissions import effective_role
from apps.events.permissions import DEFAULTS,permits
from .event_scope import event_id, navigation_context
from .protected_media import protected_media_response


def event_open(event):
    if event.state not in ['OPEN','RUNNING']:
        raise PermissionDenied('O evento não está aberto para ingresso.')
    if event.ends_at and event.ends_at <= timezone.now():
        raise PermissionDenied('Este evento foi encerrado. Novos ingressos não são permitidos.')


def invite_event(token, event_id=None):
    try:
        signed_id = UUID(signing.loads(token, salt='event-join', max_age=60 * 60 * 24 * 30))
        if event_id is not None and UUID(str(event_id)) != signed_id:
            raise ValidationError('O UUID do evento não corresponde ao convite.')
    except (signing.BadSignature, ValueError, TypeError, AttributeError):
        raise ValidationError('Link de ingresso inválido ou expirado.')
    event = get_object_or_404(Event, pk=signed_id)
    event_open(event)
    return event


def join_event(user, event):
    event_open(event)
    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk)
        event_open(event)
        participant, created = EventParticipant.objects.get_or_create(user=user, event=event)
        ParticipantProfile.objects.get_or_create(participant=participant)
        ParticipantPreference.objects.get_or_create(participant=participant, defaults={'filters': DEFAULT_FILTERS.copy()})
        if created:
            deliver_sent_announcements(participant)
            global_profile=getattr(user,'profile',None)
            if global_profile and global_profile.recurring_reported:
                Notification.objects.bulk_create([Notification(recipient=manager,event=event,title='Perfil em acompanhamento ingressou em novo evento',body='Consulte o histórico global e decida se a organização local deve ser informada. Nenhuma restrição automática foi aplicada.') for manager in get_user_model().objects.filter(is_active=True,is_superuser=True)])
            if global_profile and global_profile.preferences.get('event_profile'):
                data=global_profile.preferences['event_profile']
                profile=participant.profile
                for source,target in {'first':'first_name','last':'last_name','month':'birth_month','year':'birth_year','gender':'gender','bio':'bio'}.items():
                    if data.get(source): setattr(profile,target,data[source])
                profile.save()
                for i,key in enumerate(global_profile.preferences.get('photos',[])[:10]):
                    ParticipantPhoto.objects.create(participant=participant,storage_key=key,position=i,is_primary=i==0,visibility='PRE_MATCH' if i<3 else 'POST_MATCH')
            log(user, 'participant.joined', participant, event)
    return participant


def access(request, moderate=False, admin=False):
    if UserSuspension.objects.filter(user=request.user).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).exists():
        raise PermissionDenied('Sua conta está suspensa.')
    identifier = event_id(request)
    if request.user.is_superuser:
        event = get_object_or_404(Event,pk=identifier)
        return SimpleNamespace(role='ADMIN',event=event,user=request.user,permissions=[],delegated_to_id=None)
    membership = get_object_or_404(EventAdministrator.objects.select_related('event', 'user'),
        user=request.user, event_id=identifier, is_active=True)
    role = effective_role(membership)
    if role not in ['ADMIN', 'MODERATOR', 'OPERATOR', 'DELEGATED'] or (moderate and not permits(membership,'reports')) or (admin and role != 'ADMIN'):
        raise PermissionDenied('Seu papel não permite esta ação.')
    membership.role = role
    return membership


def log(user, action, obj, event, **details):
    from apps.audit.services import record
    with transaction.atomic():
        return record(user, action, obj, event, **details)


def navigation(request):
    context = navigation_context(request)
    identifier = event_id(request, required=False)
    if context == 'global' and request.user.is_superuser:
        return {'navigation':'global'}
    if context == 'global':
        raise PermissionDenied('Acesso exclusivo da Administração Global.')
    if context == 'selection':
        from .contexts import available
        return {'navigation':'selection','contexts':available(request.user)}
    if request.user.is_superuser and context == 'administration':
        event = get_object_or_404(Event, pk=identifier)
        draft = event.state == 'DRAFT'
        return {'navigation':'administration','role':'ADMIN','globalContext':True,'eventId':str(event.pk),
            'initialPage': 'event' if draft else 'dashboard'}
    if context == 'participant':
        return {'navigation':'participant'}
    membership = EventAdministrator.objects.filter(user=request.user, event_id=identifier, is_active=True).first()
    if context == 'administration' and membership is None:
        raise PermissionDenied('Você não administra este evento.')
    return {'navigation': 'administration', 'role': effective_role(membership), 'eventId':str(membership.event_id)} if membership else {'navigation': 'participant'}


def suspension_q():
    return Q(revoked_at__isnull=True) & (Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()))


def admin_participants(event, moderate, now):
    """Everything used by a participant card, in a fixed number of queries."""
    participants = event.participants.select_related('user', 'profile', 'event', 'ban').annotate(
        has_current_user_suspension=Exists(UserSuspension.objects.filter(user_id=OuterRef('user_id')).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now))),
    ).prefetch_related(
        Prefetch('event_suspensions', EventSuspension.objects.filter(revoked_at__isnull=True).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)).order_by('pk'), to_attr='current_event_suspensions'),
        Prefetch('photos', ParticipantPhoto.objects.filter(
            visibility='PRE_MATCH', is_primary=True, removed_at__isnull=True,
        ).order_by('pk'), to_attr='admin_primary_photos'),
    )
    if moderate:
        # Independent aggregates avoid a reports x blocks join for every person.
        reports = Report.objects.filter(
            reported_id=OuterRef('pk'), is_unfounded=False, is_administrative=False,
        ).order_by().values('reported_id').annotate(total=Count('pk')).values('total')
        blocks = Block.objects.filter(target_id=OuterRef('pk')).order_by().values(
            'target_id',
        ).annotate(total=Count('pk')).values('total')
        participants = participants.annotate(
            reports_count=Coalesce(Subquery(reports), 0),
            blocks_count=Coalesce(Subquery(blocks), 0),
        ).prefetch_related(Prefetch('blocks_received', Block.objects.filter(
            participant__event=event,
        ).only('id', 'target_id', 'created_at').order_by('created_at', 'pk'), to_attr='event_block_signals'))
    return participants.order_by('created_at', 'pk')


def participant_payload(p, moderate):
    profile = getattr(p, 'profile', None)
    suspensions = getattr(p, 'current_event_suspensions', None)
    suspension = (suspensions[0] if suspensions else None) if suspensions is not None else p.event_suspensions.filter(suspension_q()).first()
    ban = p.active_ban
    photos = getattr(p, 'admin_primary_photos', None)
    photo = (photos[0] if photos else None) if photos is not None else p.photos.filter(visibility='PRE_MATCH', is_primary=True,removed_at__isnull=True).first()
    return {'id': str(p.pk), 'name': (f'{profile.first_name} {profile.last_name}'.strip() if profile else '') or p.user.email,
        'age': age(profile) if profile else None, 'job': profile.job if profile else '',
        'email': p.user.email, 'created': p.created_at, 'updated': p.updated_at,
        'lastSeen': p.last_seen_at, 'online': p.activity_is_recent(), 'presence': p.current_presence,
        'image': (photo.storage_key if photo.storage_key.startswith('/images/') else f'/api/events/{p.event_id}/event-admin/photos/{photo.pk}/content/') if photo else '/images/profile-placeholder.svg',
        'status': p.operational_status,
        'reason': (ban.reason if ban else suspension.reason if suspension else '') if moderate else '',
        'reports': (p.reports_count if hasattr(p, 'reports_count') else p.reports_received.filter(is_unfounded=False,is_administrative=False).count()) if moderate else None,
        'blocks': (p.blocks_count if hasattr(p, 'blocks_count') else p.blocks_received.count()) if moderate else None}


def case_payload(case, participants=None, history=None, event_id=None):
    report = case.report
    def participant(p_id, related):
        return participants[p_id] if participants is not None else participant_payload(getattr(report, related), True)
    notes = getattr(case, 'admin_notes', None)
    if notes is None:
        notes = case.case_notes.select_related('author').order_by('created_at')
    if history is None:
        history = AuditLog.objects.filter(object_label=case._meta.label, object_id=case.pk).select_related('actor').order_by('created_at')
    labels = {'case.created': 'Ocorrência criada', 'case.assume': 'Ocorrência assumida',
        'case.note': 'Nota interna adicionada', 'case.resolve': 'Ocorrência resolvida',
        'case.suspend': 'Participante suspenso; caso em acompanhamento', 'case.ban': 'Participante banido do evento',
        'case.reopen': 'Ocorrência reaberta'}
    return {'id': str(case.pk), 'reference': str(case.pk)[:8].upper(), 'reason': report.reason,
        'description': report.description or report.reason, 'kind': 'Administrativa' if report.is_administrative else 'Denúncia', 'priority': case.priority,
        'reported': participant(report.reported_id, 'reported'), 'reporter': participant(report.reporter_id, 'reporter') if report.reporter_id else None,
        'author': participant(report.reporter_id, 'reporter')['email'] if report.reporter_id else report.created_by.email if report.created_by_id else 'Administração',
        'status': 'Resolvida' if case.closed_at else 'Em análise' if case.assigned_to_id else 'Pendente',
        'created': case.created_at, 'closed': case.closed_at,
        'unfounded':report.is_unfounded,
        'responsible': case.assigned_to.email if case.assigned_to_id else None,
        'notes': [{'id': str(n.pk), 'author': n.author.email, 'body': n.body, 'created': n.created_at} for n in notes],
        'history': [{'id': str(a.pk), 'author': a.actor.email if a.actor_id else 'Sistema',
            'body': labels.get(a.action, a.action) + (': ' + a.details['reason'] if a.details.get('reason') else ''),
            'created': a.created_at} for a in history],
        'evidence': [{'id': str(e.pk), 'description': e.description, 'snapshot':e.snapshot, 'content': f'/api/events/{event_id or report.reported.event_id}/event-admin/evidence/{e.pk}/content/' if e.storage_key else None} for e in report.evidence.all()]}


class JoinView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        event = invite_event(token, request.query_params.get('event'))
        return Response({'id': str(event.pk), 'name': event.name, 'starts': event.starts_at, 'ends': event.ends_at})

    def post(self, request, token):
        if not request.user.is_authenticated:
            raise PermissionDenied('Entre ou crie uma conta para ingressar.')
        event = invite_event(token, request.data.get('event', request.query_params.get('event')))
        participant = join_event(request.user, event)
        from .services import current, bootstrap
        request.session['event_id'] = str(event.pk)
        request.session['navigation'] = 'participant'
        request.selected_context = {'navigation':'participant','event':str(event.pk)}
        return Response({**bootstrap(current(request)), 'navigation': 'participant'})


class AdminBootstrapView(APIView):
    def get(self, request):
        member = access(request)
        event = member.event
        moderate = permits(member,'reports')
        now = timezone.now()
        participants_query = event.participants.all()
        suspended_ids = EventSuspension.objects.filter(suspension_q(), participant__event=event).values_list('participant_id', flat=True)
        global_suspended=UserSuspension.objects.filter(Q(ends_at__isnull=True)|Q(ends_at__gt=now)).values_list('user_id',flat=True)
        activity_minutes = event.location_interval_minutes if event.mode == 'ONLINE' else 5
        active_count = participants_query.filter(is_active=True, user__is_active=True,last_seen_at__gte=now-timedelta(minutes=activity_minutes)).filter(Q(ban__isnull=True)|Q(ban__revoked_at__isnull=False)).exclude(pk__in=suspended_ids).exclude(user_id__in=global_suspended).count()
        participants = list(admin_participants(event, moderate, now))
        participant_data = {p.pk: participant_payload(p, moderate) for p in participants}
        cases = list(ModerationCase.objects.filter(Q(report__reporter__event=event) | Q(report__is_administrative=True, report__reporter__isnull=True), report__reported__event=event).select_related(
            'report__created_by', 'assigned_to',
        ).prefetch_related(
            Prefetch('case_notes', ModerationNote.objects.select_related('author').order_by('created_at', 'pk'), to_attr='admin_notes'),
            'report__evidence',
        ).order_by('-created_at', 'pk')) if moderate else []
        case_history = {case.pk: [] for case in cases}
        if cases:
            for entry in AuditLog.objects.filter(object_label=ModerationCase._meta.label, object_id__in=case_history).select_related('actor').order_by('created_at', 'pk'):
                case_history[entry.object_id].append(entry)
        token = signing.dumps(str(event.pk), salt='event-join')
        return Response({'navigation': 'administration', 'role': member.role,
            'permissions':sorted(DEFAULTS.get(member.role,set())|set(member.permissions)),
            'globalContext':request.user.is_superuser,
            'events': [{'id':str(e.pk),'name':e.name,'role':'ADMIN'} for e in Event.objects.all()] if request.user.is_superuser else [{'id': str(m.event_id), 'name': m.event.name, 'role': m.role} for m in request.user.event_administrations.filter(is_active=True).select_related('event')],
            'event': {'id': str(event.pk), 'name': event.name, 'description': event.description,
                'starts': event.starts_at, 'ends': event.ends_at,
                'responsible': [m.user.get_full_name() or m.user.email for m in event.administrators.filter(role='ADMIN').select_related('user')],
                'state': event.state, 'status': event.get_state_display(), 'mode': event.mode,
                  'joinPath': None if event.state not in ['OPEN','RUNNING'] or (event.ends_at and event.ends_at <= now) else '/?invite=' + token},
            'participants': list(participant_data.values()),
            'cases': [case_payload(c, participant_data, case_history[c.pk], event.pk) for c in cases],
            'metrics': {'participants': len(participants), 'active': active_count,
                'new': sum(p.created_at >= now-timedelta(hours=1) for p in participants),
                'matches': Match.objects.filter(participant__event=event).count(),
                'conversations': Conversation.objects.filter(match__participant__event=event).count(),
                'blocks': Block.objects.filter(participant__event=event, target__event=event).count() if moderate else None} if member.role=='ADMIN' else {key:None for key in ['participants','active','new','matches','conversations','blocks']},
            'team': [{'id': str(m.pk), 'name': m.user.get_full_name() or m.user.email, 'role': m.get_role_display()} for m in event.administrators.select_related('user')],
            'blockSignals': [{'participant': participant_data[p.pk], 'timeline': [block.created_at for block in p.event_block_signals]} for p in participants if moderate and p.event_block_signals],
        })

    def post(self, request):
        if request.user.is_superuser:
            event = get_object_or_404(Event,pk=request.data.get('event'))
        else:
            event = get_object_or_404(EventAdministrator,user=request.user,event_id=request.data.get('event'),is_active=True).event
        request.session['event_id'] = str(event.pk)
        request.session['navigation'] = 'administration'
        request.selected_context = {'navigation':'administration','event':str(event.pk)}
        return Response(navigation(request))


def sanction(request, participant, action, reason, member):
    if action == 'ban' and member.role != 'ADMIN':
        raise PermissionDenied('Somente administradores podem banir do evento.')
    if action == 'ban':
        if request.data.get('confirmed') is not True:
            raise ValidationError('Confirme explicitamente o banimento.')
        EventBan.objects.update_or_create(participant=participant, defaults={'reason':reason,'revoked_at':None,'revoked_by':None,'revocation_reason':'','location_anomaly':None})
    elif action == 'suspend':
        if participant.active_ban:
            raise ValidationError('Participante já banido.')
        if not participant.event_suspensions.filter(suspension_q()).exists():
            EventSuspension.objects.create(participant=participant, actor=request.user, reason=reason)
    elif action == 'reactivate':
        participant.event_suspensions.filter(suspension_q()).update(revoked_at=timezone.now())
    else:
        raise ValidationError('Ação inválida.')
    log(request.user, 'participant.' + action, participant, member.event, reason=reason)


class AdminParticipantActionView(APIView):
    def post(self, request, participant_id):
        member = access(request, moderate=request.data.get('action')!='report')
        if member.event.state in ['CLOSED','ARCHIVED']:
            raise PermissionDenied('Dados operacionais em modo somente leitura após o encerramento.')
        reason = str(request.data.get('reason', '')).strip()
        if not reason or len(reason) > 4000:
            raise ValidationError('Informe motivo e contexto da decisão (até 4.000 caracteres).')
        with transaction.atomic():
            participant = get_object_or_404(EventParticipant.objects.select_for_update(), pk=participant_id, event=member.event)
            action = request.data.get('action')
            if action == 'report':
                if participant.user_id == request.user.pk:
                    raise ValidationError('Não é permitido abrir ocorrência sobre si mesmo.')
                category = str(request.data.get('category', '')).strip()
                if len(category) > 200:
                    raise ValidationError('Motivo deve ter até 200 caracteres.')
                report = Report.objects.create(created_by=request.user, reported=participant, reason=category or 'Ocorrência administrativa', description=reason, is_administrative=True)
                case = ModerationCase.objects.create(report=report)
                ModerationAction.objects.create(case=case, actor=request.user, description='Ocorrência administrativa criada: ' + reason)
                recipients = get_user_model().objects.filter(Q(event_administrations__event=member.event, event_administrations__role__in=['ADMIN', 'MODERATOR']) | Q(is_superuser=True), is_active=True).distinct()
                Notification.objects.bulk_create([Notification(recipient=user, event=member.event,
                    title='Nova ocorrência de moderação', body=f'Ocorrência #{str(case.pk)[:8].upper()} requer análise no evento {member.event.name}.') for user in recipients])
                ModerationAction.objects.create(case=case, actor=request.user, description='Notificações internas registradas para a moderação do evento e administração global disponível.')
                log(request.user, 'case.created', case, member.event)
            else:
                sanction(request, participant, action, reason, member)
        return Response({'ok': True})


class AdminCaseActionView(APIView):
    def post(self, request, case_id):
        member = access(request, moderate=True)
        if member.event.state in ['CLOSED','ARCHIVED']:
            raise PermissionDenied('Dados operacionais em modo somente leitura após o encerramento.')
        action = request.data.get('action')
        reason = str(request.data.get('reason', '')).strip()
        if action != 'assume' and (not reason or len(reason) > 4000):
            raise ValidationError('Informe a justificativa (até 4.000 caracteres).')
        with transaction.atomic():
            case = get_object_or_404(ModerationCase.objects.select_for_update(of=('self',)).filter(Q(report__reporter__event=member.event) | Q(report__is_administrative=True, report__reporter__isnull=True)), pk=case_id,
                report__reported__event=member.event)
            if action == 'reopen':
                if member.role != 'ADMIN':
                    raise PermissionDenied('Somente administradores podem reabrir ocorrências.')
                if not case.closed_at:
                    raise ValidationError('Esta ocorrência já está aberta.')
                case.closed_at = None
            elif case.closed_at:
                raise ValidationError('Reabra a ocorrência antes de alterá-la.')
            elif action == 'assume':
                if case.assigned_to_id and case.assigned_to_id != request.user.pk:
                    raise ValidationError('Esta ocorrência já possui responsável.')
                case.assigned_to = request.user
            elif action == 'note':
                ModerationNote.objects.create(case=case, author=request.user, body=reason)
            elif action == 'resolve':
                case.closed_at = timezone.now()
                if 'unfounded' in request.data:
                    case.report.is_unfounded=request.data['unfounded'] is True;case.report.save(update_fields=['is_unfounded','updated_at'])
            elif action in ['suspend', 'ban']:
                participant = EventParticipant.objects.select_for_update().get(pk=case.report.reported_id)
                sanction(request, participant, action, reason, member)
                # Sanctions remain under review until explicitly resolved.
            else:
                raise ValidationError('Ação inválida.')
            case.save()
            labels = {'assume': 'Ocorrência assumida', 'note': 'Nota adicionada', 'resolve': 'Resolvida sem nova sanção',
                'suspend': 'Participante suspenso; caso em acompanhamento', 'ban': 'Participante banido do evento', 'reopen': 'Ocorrência reaberta'}
            ModerationAction.objects.create(case=case, actor=request.user, description=labels[action] + (': ' + reason if reason else ''))
            log(request.user, 'case.' + action, case, member.event, reason=reason)
        return Response({'ok': True})


class AdminEvidenceContentView(APIView):
    def get(self, request, evidence_id):
        member = access(request, moderate=True)
        evidence = get_object_or_404(ReportEvidence.objects.filter(Q(report__reporter__event=member.event) | Q(report__is_administrative=True, report__reporter__isnull=True)), pk=evidence_id,
            report__reported__event=member.event)
        if not evidence.storage_key:
            raise Http404
        response = protected_media_response(evidence.storage_key, as_attachment=True)
        try:
            log(request.user, 'evidence.viewed', evidence, member.event)
        except Exception:
            if response.streaming:
                response.file_to_stream.close()
            raise
        return response


class AdminParticipantProfileView(APIView):
    def get(self, request, participant_id):
        member = access(request)
        participant = get_object_or_404(EventParticipant.objects.select_related('user', 'profile', 'event'),
            pk=participant_id, event=member.event)
        from .services import person_payload, ordered_photos
        payload = person_payload(participant)
        profile = getattr(participant, 'profile', None)
        payload['name'] = (f'{profile.first_name} {profile.last_name}'.strip() if profile else '') or participant.user.email
        photos = [photo for photo in ordered_photos(participant) if photo.visibility == 'PRE_MATCH']
        def url(photo):
            return photo.storage_key if photo.storage_key.startswith('/images/') else f'/api/events/{participant.event_id}/event-admin/photos/{photo.pk}/content/'
        primary = next((photo for photo in photos if photo.is_primary), None)
        payload['image'] = url(primary) if primary else '/images/profile-placeholder.svg'
        payload['photos'] = [url(photo) for photo in photos]
        return Response(payload)


class AdminPhotoContentView(APIView):
    def get(self, request, photo_id):
        member = access(request)
        photo = get_object_or_404(ParticipantPhoto, pk=photo_id, participant__event=member.event, visibility='PRE_MATCH',removed_at__isnull=True)
        if photo.storage_key.startswith('/images/'):
            raise Http404
        return protected_media_response(photo.storage_key)
