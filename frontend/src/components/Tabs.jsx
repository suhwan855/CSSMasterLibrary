import React from "react";

export default function Tabs({ tabs, activeTab, setActiveTab }) {
  return (
    <div className="tabbar">
      {tabs.map(({ id, label }) => (
        <button
          key={id}
          className={activeTab === id ? "active" : ""}
          onClick={() => setActiveTab(id)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
