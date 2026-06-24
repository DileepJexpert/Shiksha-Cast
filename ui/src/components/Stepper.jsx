export default function Stepper({ current }) {
  const steps = ['Upload slides', 'Write script & voice', 'Build & download'];
  return (
    <div className="stepper">
      {steps.map((label, i) => {
        const n = i + 1;
        const state = n < current ? 'done' : n === current ? 'active' : 'todo';
        return (
          <div key={n} className={`step step-${state}`}>
            <span className="step-num">{n < current ? '✓' : n}</span>
            <span className="step-label">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
