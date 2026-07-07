export function BackgroundEffects() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      {/* Dot pattern */}
      <div className="dot-pattern absolute inset-0" />

      {/* Gradient orbs */}
      <div className="glow-orb top-[-200px] left-1/4 h-[600px] w-[600px] bg-teal-500/15" />
      <div className="glow-orb top-[40%] right-[-100px] h-[400px] w-[400px] bg-cyan-500/10" />
      <div className="glow-orb bottom-[-100px] left-1/3 h-[300px] w-[300px] bg-teal-500/10" />
    </div>
  );
}
