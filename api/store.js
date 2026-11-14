export const find=(db,id)=>db.prepare('SELECT * FROM sessions WHERE id=?').bind(id).first();
export async function create(db,row,now) {
  const result=await db.prepare(`INSERT OR IGNORE INTO sessions
    (id,read_hash,write_hash,payload,created_at,updated_at,expires_at,hard_expires_at,completed_at)
    SELECT ?,?,?,?,?,?,?,?,? WHERE ABS((julianday('now')-2440587.5)*86400000-?)<300000 AND (SELECT COUNT(*) FROM sessions WHERE expires_at>? AND revoked=0)<500`)
    .bind(row.id,row.read_hash,row.write_hash,row.payload,now,now,row.expires_at,row.hard_expires_at,row.completed_at,parseInt(row.id.slice(0,12),16),now).run();
  return result.meta.changes===1;
}
export async function update(db,id,version,payload,times,now) {
  const result=await db.prepare(`UPDATE sessions SET payload=?,version=version+1,updated_at=?,expires_at=?,completed_at=?
    WHERE id=? AND version=? AND expires_at>? AND revoked=0 AND (completed_at IS NULL OR ?='Concluído')`)
    .bind(JSON.stringify(payload),now,times.expires,times.completed,id,version,now,payload.status).run();
  return result.meta.changes===1;
}
export const revoke=(db,id,now)=>db.prepare('UPDATE sessions SET revoked=1,expires_at=? WHERE id=?').bind(now,id).run();
export const cancel=(db,id,write_hash,now)=>db.prepare(`INSERT OR IGNORE INTO sessions
  (id,read_hash,write_hash,payload,created_at,updated_at,expires_at,hard_expires_at,revoked)
  VALUES (?,'',?,'{}',?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET revoked=1,expires_at=excluded.expires_at WHERE sessions.write_hash=excluded.write_hash`).bind(id,write_hash,now,now,now,now+86400000).run();
export const cleanup=(db,now)=>db.prepare('DELETE FROM sessions WHERE id IN (SELECT id FROM sessions WHERE expires_at<=? AND created_at<=? ORDER BY expires_at LIMIT 500)').bind(now,now-600000).run();
