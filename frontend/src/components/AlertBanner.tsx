interface Props {
  alerts: string[];
}

export function AlertBanner({ alerts }: Props) {
  if (alerts.length === 0) return null;

  return (
    <div className="rounded-xl bg-amber-950/40 border border-amber-700/40 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-2">Health Alerts</p>
      <ul className="flex flex-col gap-1">
        {alerts.map((a, i) => (
          <li key={i} className="text-sm text-amber-200">
            {a}
          </li>
        ))}
      </ul>
    </div>
  );
}
