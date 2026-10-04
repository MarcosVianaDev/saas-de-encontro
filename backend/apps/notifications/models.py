from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Notification(BaseModel):
    kind = models.CharField(max_length=50,blank=True)
    action_path = models.CharField(max_length=500,blank=True)
    dedupe_key = models.CharField(max_length=200,unique=True,null=True,blank=True)
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="notifications", null=True, blank=True)
    recipient = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='administrative_notifications', null=True, blank=True)
    event = models.ForeignKey('events.Event', on_delete=models.PROTECT, related_name='administrative_notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)


class EventAnnouncement(BaseModel):
    event = models.ForeignKey('events.Event',on_delete=models.PROTECT,related_name='announcements')
    author = models.ForeignKey('accounts.User',on_delete=models.PROTECT,related_name='+')
    title = models.CharField(max_length=200)
    body = models.TextField()
    url = models.URLField(blank=True)
    scheduled_at = models.DateTimeField(null=True,blank=True)
    sent_at = models.DateTimeField(null=True,blank=True)
    state = models.CharField(max_length=12,default='DRAFT',choices=[('DRAFT','Rascunho'),('SCHEDULED','Agendado'),('SENT','Enviado'),('HELD','Pausado'),('CANCELLED','Não enviado')])


class SupportThread(BaseModel):
    participant = models.ForeignKey('participants.EventParticipant',on_delete=models.PROTECT,related_name='support_threads')
    subject = models.CharField(max_length=200)
    closed_at = models.DateTimeField(null=True,blank=True)


class SupportMessage(BaseModel):
    thread = models.ForeignKey(SupportThread,on_delete=models.PROTECT,related_name='messages')
    author = models.ForeignKey('accounts.User',on_delete=models.PROTECT,related_name='+')
    body = models.TextField()
