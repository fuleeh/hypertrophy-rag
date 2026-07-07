export function BackgroundEffects() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="glow-orb top-[-200px] left-1/4 h-[500px] w-[500px] bg-teal-500/8" />
      <div className="glow-orb top-[40%] right-[-100px] h-[350px] w-[350px] bg-cyan-500/5" />
    </div>
  );
}
