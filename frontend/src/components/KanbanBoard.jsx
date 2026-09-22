import { useState } from "react";
import JobCard from "./JobCard";
import { KANBAN_COLUMNS } from "../statusMeta";
import "./KanbanBoard.css";

export default function KanbanBoard({ jobs, onStatusChange }) {
  const [dragOverColumn, setDragOverColumn] = useState(null);
  const [draggingJob, setDraggingJob] = useState(null);

  const handleDragStart = (e, job) => {
    setDraggingJob(job);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDrop = (column) => {
    if (draggingJob && !column.statuses.includes(draggingJob.status)) {
      // Land on the first (most specific) status in that column,
      // e.g. dropping into "Interviewing" defaults to "Phone Screen".
      onStatusChange(draggingJob.id, column.statuses[0]);
    }
    setDragOverColumn(null);
    setDraggingJob(null);
  };

  return (
    <div className="kanban-board">
      {KANBAN_COLUMNS.map((column) => {
        const columnJobs = jobs.filter((j) => column.statuses.includes(j.status));
        return (
          <div
            key={column.key}
            className={"kanban-column" + (dragOverColumn === column.key ? " is-drag-over" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOverColumn(column.key);
            }}
            onDragLeave={() => setDragOverColumn((c) => (c === column.key ? null : c))}
            onDrop={() => handleDrop(column)}
          >
            <div className="kanban-column-header">
              <h3>{column.label}</h3>
              <span className="kanban-column-count">{columnJobs.length}</span>
            </div>
            <div className="kanban-column-body">
              {columnJobs.length === 0 ? (
                <p className="kanban-column-empty">Nothing here</p>
              ) : (
                columnJobs.map((job) => (
                  <JobCard key={job.id} job={job} onDragStart={handleDragStart} />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
