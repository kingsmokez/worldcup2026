import { useRef, useEffect, useState } from 'react';
import type { PlayerData } from '../hooks/useData';

interface FormationTeamProps {
  teamCode: string;
  teamNameZh: string;
  formation: string;
  players: PlayerData[];
  flagEmoji?: string;
}

interface PlayerSlot {
  number: number;
  x: number;
  y: number;
  name: string;
  nameZh: string;
  position: string;
  positionZh: string;
}

// Formation position templates (x: 0=left, 1=right; y: 0=top/attack, 1=bottom/defense)
const FORMATION_POSITIONS: Record<string, { x: number; y: number; pos: string }[]> = {
  '4-3-3': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.82, y: 0.73, pos: 'RB' },
    { x: 0.62, y: 0.75, pos: 'CB' },
    { x: 0.38, y: 0.75, pos: 'CB' },
    { x: 0.18, y: 0.73, pos: 'LB' },
    { x: 0.68, y: 0.52, pos: 'CM' },
    { x: 0.5, y: 0.48, pos: 'CM' },
    { x: 0.32, y: 0.52, pos: 'CM' },
    { x: 0.82, y: 0.28, pos: 'RW' },
    { x: 0.5, y: 0.2, pos: 'ST' },
    { x: 0.18, y: 0.28, pos: 'LW' },
  ],
  '4-4-2': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.82, y: 0.73, pos: 'RB' },
    { x: 0.62, y: 0.75, pos: 'CB' },
    { x: 0.38, y: 0.75, pos: 'CB' },
    { x: 0.18, y: 0.73, pos: 'LB' },
    { x: 0.82, y: 0.5, pos: 'RM' },
    { x: 0.62, y: 0.52, pos: 'CM' },
    { x: 0.38, y: 0.52, pos: 'CM' },
    { x: 0.18, y: 0.5, pos: 'LM' },
    { x: 0.62, y: 0.25, pos: 'ST' },
    { x: 0.38, y: 0.25, pos: 'ST' },
  ],
  '3-5-2': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.68, y: 0.75, pos: 'CB' },
    { x: 0.5, y: 0.77, pos: 'CB' },
    { x: 0.32, y: 0.75, pos: 'CB' },
    { x: 0.88, y: 0.52, pos: 'RWB' },
    { x: 0.65, y: 0.5, pos: 'CM' },
    { x: 0.5, y: 0.45, pos: 'CAM' },
    { x: 0.35, y: 0.5, pos: 'CM' },
    { x: 0.12, y: 0.52, pos: 'LWB' },
    { x: 0.62, y: 0.24, pos: 'ST' },
    { x: 0.38, y: 0.24, pos: 'ST' },
  ],
  '4-2-3-1': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.82, y: 0.73, pos: 'RB' },
    { x: 0.62, y: 0.75, pos: 'CB' },
    { x: 0.38, y: 0.75, pos: 'CB' },
    { x: 0.18, y: 0.73, pos: 'LB' },
    { x: 0.6, y: 0.55, pos: 'CDM' },
    { x: 0.4, y: 0.55, pos: 'CDM' },
    { x: 0.82, y: 0.35, pos: 'RAM' },
    { x: 0.5, y: 0.32, pos: 'CAM' },
    { x: 0.18, y: 0.35, pos: 'LAM' },
    { x: 0.5, y: 0.15, pos: 'ST' },
  ],
  '5-3-2': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.88, y: 0.7, pos: 'RWB' },
    { x: 0.68, y: 0.75, pos: 'CB' },
    { x: 0.5, y: 0.77, pos: 'CB' },
    { x: 0.32, y: 0.75, pos: 'CB' },
    { x: 0.12, y: 0.7, pos: 'LWB' },
    { x: 0.65, y: 0.5, pos: 'CM' },
    { x: 0.5, y: 0.48, pos: 'CM' },
    { x: 0.35, y: 0.5, pos: 'CM' },
    { x: 0.62, y: 0.24, pos: 'ST' },
    { x: 0.38, y: 0.24, pos: 'ST' },
  ],
  '4-1-4-1': [
    { x: 0.5, y: 0.92, pos: 'GK' },
    { x: 0.82, y: 0.73, pos: 'RB' },
    { x: 0.62, y: 0.75, pos: 'CB' },
    { x: 0.38, y: 0.75, pos: 'CB' },
    { x: 0.18, y: 0.73, pos: 'LB' },
    { x: 0.5, y: 0.58, pos: 'CDM' },
    { x: 0.82, y: 0.42, pos: 'RM' },
    { x: 0.62, y: 0.4, pos: 'CM' },
    { x: 0.38, y: 0.4, pos: 'CM' },
    { x: 0.18, y: 0.42, pos: 'LM' },
    { x: 0.5, y: 0.18, pos: 'ST' },
  ],
};

// Map position codes to prioritize player assignment
const POS_PRIORITY: Record<string, string[]> = {
  GK: ['GK'],
  CB: ['CB'],
  RB: ['RB', 'RWB'],
  LB: ['LB', 'LWB'],
  RWB: ['RWB', 'RB'],
  LWB: ['LWB', 'LB'],
  CDM: ['CDM', 'CM', 'DM'],
  CM: ['CM', 'CDM', 'CAM'],
  CAM: ['CAM', 'CM', 'CF'],
  RM: ['RM', 'RW', 'RWB'],
  LM: ['LM', 'LW', 'LWB'],
  RAM: ['RAM', 'RW', 'RM'],
  LAM: ['LAM', 'LW', 'LM'],
  RW: ['RW', 'RM', 'RF'],
  LW: ['LW', 'LM', 'LF'],
  RF: ['RF', 'RW', 'ST'],
  LF: ['LF', 'LW', 'ST'],
  CF: ['CF', 'ST', 'CAM'],
  ST: ['ST', 'CF', 'CAM'],
};

function assignPlayersToFormation(
  formation: string,
  players: PlayerData[]
): PlayerSlot[] {
  const positions = FORMATION_POSITIONS[formation] || FORMATION_POSITIONS['4-3-3'];
  const used = new Set<number>();
  const result: PlayerSlot[] = [];

  for (const pos of positions) {
    const preferred = POS_PRIORITY[pos.pos] || [pos.pos];
    let assigned: PlayerData | null = null;

    for (const pref of preferred) {
      // First try exact match
      for (let i = 0; i < players.length; i++) {
        if (used.has(i)) continue;
        if (players[i].position === pref) {
          assigned = players[i];
          used.add(i);
          break;
        }
      }
      if (assigned) break;

      // Then try partial match
      for (let i = 0; i < players.length; i++) {
        if (used.has(i)) continue;
        if (players[i].position.includes(pref) || pref.includes(players[i].position)) {
          assigned = players[i];
          used.add(i);
          break;
        }
      }
      if (assigned) break;
    }

    // Fallback: pick next unused player
    if (!assigned) {
      for (let i = 0; i < players.length; i++) {
        if (used.has(i)) continue;
        assigned = players[i];
        used.add(i);
        break;
      }
    }

    result.push({
      number: assigned?.number || 0,
      x: pos.x,
      y: pos.y,
      name: assigned?.name || '???',
      nameZh: assigned?.name_zh || '???',
      position: pos.pos,
      positionZh: assigned?.position_zh || pos.pos,
    });
  }

  return result;
}

// ─── Single Team Formation Component ───
function TeamFormation({ teamCode, teamNameZh, formation, players, flagEmoji }: FormationTeamProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hovered, setHovered] = useState<PlayerSlot | null>(null);
  const [selectedFormation, setSelectedFormation] = useState(formation);

  const availableFormations = Object.keys(FORMATION_POSITIONS);
  const activeFormation = availableFormations.includes(selectedFormation) ? selectedFormation : '4-3-3';
  const slots = assignPlayersToFormation(activeFormation, players);

  useEffect(() => {
    drawPitch(canvasRef, slots);
  }, [activeFormation, players]);

  return (
    <div className="formation-team-block">
      {/* Team header */}
      <div className="formation-team-header">
        <span className="formation-team-flag">{flagEmoji}</span>
        <span className="formation-team-name">{teamNameZh}</span>
      </div>

      {/* Formation selector */}
      <div className="formation-selector">
        {availableFormations.map((f) => (
          <button
            key={f}
            className={`formation-option ${f === activeFormation ? 'formation-option-active' : ''}`}
            onClick={() => setSelectedFormation(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Canvas pitch */}
      <div className="formation-canvas-wrap">
        <canvas
          ref={canvasRef}
          width={400}
          height={560}
          className="formation-canvas"
          onMouseMove={(e) => handleCanvasHover(e, canvasRef, slots, setHovered)}
          onMouseLeave={() => setHovered(null)}
        />
        {hovered && (
          <div className="formation-tooltip">
            <span className="formation-tooltip-number">#{hovered.number}</span>
            <span className="formation-tooltip-name">{hovered.nameZh}</span>
            <span className="formation-tooltip-pos">{hovered.positionZh}</span>
          </div>
        )}
      </div>

      {/* Player list */}
      <div className="formation-player-list">
        {slots.map((s) => (
          <div key={s.number} className="formation-player-item">
            <span className="formation-player-num">{s.number}</span>
            <span className="formation-player-name">{s.nameZh}</span>
            <span className="formation-player-pos">{s.positionZh}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Formation Component (used by MatchAnalysis) ───
interface FormationTabProps {
  team1Code: string;
  team1NameZh: string;
  team1Formation: string;
  team1Players: PlayerData[];
  team1Flag?: string;
  team2Code: string;
  team2NameZh: string;
  team2Formation: string;
  team2Players: PlayerData[];
  team2Flag?: string;
}

export default function Formation(props: FormationTabProps) {
  return (
    <div className="formation-compare">
      <TeamFormation
        teamCode={props.team1Code}
        teamNameZh={props.team1NameZh}
        formation={props.team1Formation || '4-3-3'}
        players={props.team1Players}
        flagEmoji={props.team1Flag}
      />
      <TeamFormation
        teamCode={props.team2Code}
        teamNameZh={props.team2NameZh}
        formation={props.team2Formation || '4-3-3'}
        players={props.team2Players}
        flagEmoji={props.team2Flag}
      />
    </div>
  );
}

// ─── Canvas Drawing ───
function drawPitch(canvasRef: React.RefObject<HTMLCanvasElement | null>, players: PlayerSlot[]) {
  const canvas = canvasRef.current;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  const m = 16; // margin

  ctx.clearRect(0, 0, w, h);

  // Pitch background - dark green
  const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
  bgGrad.addColorStop(0, '#0a4a2e');
  bgGrad.addColorStop(0.5, '#0d5c38');
  bgGrad.addColorStop(1, '#0a4a2e');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, w, h);

  // Grass stripes
  ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
  for (let i = 0; i < w; i += 24) {
    if ((i / 24) % 2 === 0) ctx.fillRect(i, 0, 12, h);
  }

  // Pitch lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 1.5;

  // Outline
  ctx.strokeRect(m, m, w - m * 2, h - m * 2);

  // Halfway line
  ctx.beginPath();
  ctx.moveTo(m, h / 2);
  ctx.lineTo(w - m, h / 2);
  ctx.stroke();

  // Center circle
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 50, 0, Math.PI * 2);
  ctx.stroke();

  // Center dot
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 3, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.fill();

  // Penalty areas
  const paW = 160;
  const paH = 65;
  const paX = (w - paW) / 2;
  ctx.strokeRect(paX, m, paW, paH);
  ctx.strokeRect(paX, h - m - paH, paW, paH);

  // Goal areas
  const gaW = 70;
  const gaH = 22;
  const gaX = (w - gaW) / 2;
  ctx.strokeRect(gaX, m, gaW, gaH);
  ctx.strokeRect(gaX, h - m - gaH, gaW, gaH);

  // Penalty spots
  ctx.beginPath();
  ctx.arc(w / 2, m + paH - 15, 2, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(w / 2, h - m - paH + 15, 2, 0, Math.PI * 2);
  ctx.fill();

  // Goals (nets)
  const goalW = 36;
  const goalX = (w - goalW) / 2;
  ctx.strokeStyle = 'rgba(255,255,255,0.45)';
  ctx.lineWidth = 2;
  ctx.strokeRect(goalX, m - 5, goalW, 5);
  ctx.strokeRect(goalX, h - m, goalW, 5);

  // Draw players
  players.forEach((player) => {
    const px = m + player.x * (w - m * 2);
    const py = m + player.y * (h - m * 2);

    // Glow
    const glowGrad = ctx.createRadialGradient(px, py, 0, px, py, 22);
    glowGrad.addColorStop(0, 'rgba(212, 168, 67, 0.25)');
    glowGrad.addColorStop(1, 'rgba(212, 168, 67, 0)');
    ctx.beginPath();
    ctx.arc(px, py, 22, 0, Math.PI * 2);
    ctx.fillStyle = glowGrad;
    ctx.fill();

    // Player circle
    ctx.beginPath();
    ctx.arc(px, py, 14, 0, Math.PI * 2);
    const circGrad = ctx.createRadialGradient(px - 3, py - 3, 0, px, py, 14);
    circGrad.addColorStop(0, '#f0c860');
    circGrad.addColorStop(1, '#a07820');
    ctx.fillStyle = circGrad;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Number
    ctx.fillStyle = '#0a0a18';
    ctx.font = 'bold 10px "Fira Code", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(player.number), px, py);

    // Name below
    ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.font = '9px "DM Sans", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(player.nameZh, px, py + 17);
  });
}

function handleCanvasHover(
  e: React.MouseEvent<HTMLCanvasElement>,
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  players: PlayerSlot[],
  setHovered: (p: PlayerSlot | null) => void
) {
  const canvas = canvasRef.current;
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const mx = (e.clientX - rect.left) * scaleX;
  const my = (e.clientY - rect.top) * scaleY;

  const m = 16;
  const hitRadius = 18;

  for (const player of players) {
    const px = m + player.x * (canvas.width - m * 2);
    const py = m + player.y * (canvas.height - m * 2);
    const dx = mx - px;
    const dy = my - py;
    if (Math.sqrt(dx * dx + dy * dy) < hitRadius) {
      setHovered(player);
      return;
    }
  }

  setHovered(null);
}
