const STEPS = [
  { num: '1', label: 'Session Started' },
  { num: '2', label: 'Data Extracted' },
  { num: '3', label: 'Submitted' },
  { num: '4', label: 'Decision' },
];

const STATUS_PROGRESS = {
  active: 1,
  submitted_for_review: 3,
  approved: 4,
  rejected: 4,
};

export default function Stepper({ status }) {
  const currentStep = STATUS_PROGRESS[status] || 0;

  return (
    <div className="stepper">
      {STEPS.map(({ num, label }, idx) => {
        const stepNum = idx + 1;
        let dotClass, icon;
        if (stepNum < currentStep) {
          dotClass = 'done';
          icon = '✓';
        } else if (stepNum === currentStep) {
          dotClass = 'current';
          icon = num;
        } else {
          dotClass = 'pending';
          icon = num;
        }

        return (
          <div className="step" key={num}>
            <div className={`step-dot ${dotClass}`}>{icon}</div>
            <div className="step-label">{label}</div>
          </div>
        );
      })}
    </div>
  );
}
