import type { Profile, ProfileTopic } from "./types";

export function ProfileTopics({ topics, profile, onChange }: {
  topics: ProfileTopic[];
  profile: Profile;
  onChange: (profile: Profile) => void;
}) {
  return <>{topics.map((topic) => {
    const selected = profile.topicAnswers?.[topic.key] ?? (topic.key === "interests" ? profile.interests : topic.key === "purpose" && profile.purpose ? [profile.purpose] : []);
    return (
      <fieldset className="filter-card" key={topic.id}>
        <legend>{topic.name}</legend>
        <p className="microcopy">{topic.multiple ? "Selecione uma ou mais opções." : "Selecione uma opção."}</p>
        <div className="chips">
          {topic.options.map((option) => (
            <button type="button" key={option} className={`chip ${selected.includes(option) ? "active" : ""}`} aria-pressed={selected.includes(option)} onClick={() => {
              const values = selected.includes(option) ? selected.filter((value) => value !== option) : topic.multiple ? [...selected, option] : [option];
              onChange({ ...profile, topicAnswers: { ...profile.topicAnswers, [topic.key]: values },
                ...(topic.key === "interests" ? { interests: values } : {}),
                ...(topic.key === "purpose" ? { purpose: values[0] || "" } : {}),
              });
            }}>{option}</button>
          ))}
        </div>
      </fieldset>
    );
  })}</>;
}
