import React from 'react';
import { useGroups } from '../hooks/useData';
import type { GroupStandingItem } from '../hooks/useData';

const GroupStandings: React.FC = () => {
  const { data, loading, error } = useGroups();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>加载积分榜...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-message">⚠️ {error}</div>;
  }

  if (!data || !data.groups) {
    return <div className="empty-message">暂无积分榜数据</div>;
  }

  return (
    <div className="group-standings">
      <h2 className="section-title">
        <span className="title-icon">🏆</span>
        小组积分榜
      </h2>
      <div className="groups-grid">
        {data.groups.map((group) => (
          <GroupTable key={group.group} groupName={group.group} standings={group.standings} />
        ))}
      </div>
    </div>
  );
};

interface GroupTableProps {
  groupName: string;
  standings: GroupStandingItem[];
}

const GroupTable: React.FC<GroupTableProps> = ({ groupName, standings }) => {
  return (
    <div className="group-table-card">
      <h3 className="group-table-title">{groupName}组</h3>
      <div className="group-table-wrapper">
        <table className="group-table">
          <thead>
            <tr>
              <th className="col-rank">#</th>
              <th className="col-team">球队</th>
              <th className="col-num">场</th>
              <th className="col-num">胜</th>
              <th className="col-num">平</th>
              <th className="col-num">负</th>
              <th className="col-num">进/失</th>
              <th className="col-num">净</th>
              <th className="col-pts">分</th>
              <th className="col-elo" title="ELO评分">ELO</th>
            </tr>
          </thead>
          <tbody>
            {standings.length === 0 ? (
              <tr>
                <td colSpan={10} className="empty-cell">暂无数据</td>
              </tr>
            ) : (
              standings.map((team, idx) => (
                <tr key={team.code} className={idx < 2 ? 'qualify-row' : ''}>
                  <td className="col-rank">{idx + 1}</td>
                  <td className="col-team">
                    <span className="standings-flag">{team.flag_emoji}</span>
                    <span className="standings-name-zh">{team.name_zh}</span>
                    <span className="standings-name-en">{team.name}</span>
                  </td>
                  <td className="col-num">{team.played}</td>
                  <td className="col-num">{team.won}</td>
                  <td className="col-num">{team.drawn}</td>
                  <td className="col-num">{team.lost}</td>
                  <td className="col-num">{team.goals_for}/{team.goals_against}</td>
                  <td className="col-num">{team.goals_diff > 0 ? '+' : ''}{team.goals_diff}</td>
                  <td className="col-pts"><strong>{team.points}</strong></td>
                  <td className="col-elo">{team.elo_rating || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GroupStandings;