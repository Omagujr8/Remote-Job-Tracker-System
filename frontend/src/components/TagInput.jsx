import { useState } from "react";
import "./TagInput.css";

export default function TagInput({ tags, onChange }) {
  const [draft, setDraft] = useState("");

  const commit = () => {
    const value = draft.trim();
    if (value && !tags.some((t) => t.toLowerCase() === value.toLowerCase())) {
      onChange([...tags, value]);
    }
    setDraft("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit();
    } else if (e.key === "Backspace" && draft === "" && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  const removeTag = (index) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  return (
    <div className="tag-input">
      {tags.map((tag, i) => (
        <span className="tag-chip" key={`${tag}-${i}`}>
          {tag}
          <button
            type="button"
            className="tag-chip-remove"
            onClick={() => removeTag(i)}
            aria-label={`Remove tag ${tag}`}
          >
            &times;
          </button>
        </span>
      ))}
      <input
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={commit}
        placeholder={tags.length === 0 ? "Add a tag and press Enter" : ""}
        className="tag-input-field"
      />
    </div>
  );
}
