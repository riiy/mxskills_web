import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertCircle, Download, FileText, Loader2, Play, Search, Settings2 } from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://finance-skills.acquirecord.top';

async function readApiJson(response, fallbackMessage) {
  const text = await response.text();
  const trimmed = text.trim();
  let data = null;
  if (trimmed) {
    try {
      data = JSON.parse(trimmed);
    } catch {
      const status = response.status ? `HTTP ${response.status}` : 'unknown status';
      throw new Error(`${fallbackMessage}：接口返回非 JSON 内容（${status}），请检查后端 API 地址 ${API_BASE}`);
    }
  }
  if (!response.ok) {
    throw new Error(data?.detail || data?.message || `${fallbackMessage}（HTTP ${response.status}）`);
  }
  return data || {};
}

function groupSkills(skills) {
  return skills.reduce((groups, skill) => {
    const group = skill.group || '其他';
    groups[group] = groups[group] || [];
    groups[group].push(skill);
    return groups;
  }, {});
}

function MarkdownView({ content }) {
  const html = useMemo(() => {
    const raw = marked.parse(content || '暂无结果');
    return DOMPurify.sanitize(raw);
  }, [content]);
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />;
}

function SkillControls({ skill, params, setParams }) {
  if (!skill?.controls?.length) return null;
  return (
    <div className="controls">
      {skill.controls.map((control) => {
        if (control.type === 'boolean') {
          return (
            <label className="toggle" key={control.id}>
              <input
                type="checkbox"
                checked={Boolean(params[control.id])}
                onChange={(event) => setParams((prev) => ({ ...prev, [control.id]: event.target.checked }))}
              />
              <span>{control.label}</span>
            </label>
          );
        }
        if (control.type === 'select') {
          return (
            <label className="field" key={control.id}>
              <span>{control.label}</span>
              <select
                value={params[control.id] || control.options?.[0] || ''}
                onChange={(event) => setParams((prev) => ({ ...prev, [control.id]: event.target.value }))}
              >
                {control.options?.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          );
        }
        return (
          <label className="field" key={control.id}>
            <span>{control.label}</span>
            <input
              value={params[control.id] || ''}
              placeholder={control.placeholder || ''}
              onChange={(event) => setParams((prev) => ({ ...prev, [control.id]: event.target.value }))}
            />
          </label>
        );
      })}
    </div>
  );
}

function App() {
  const [skills, setSkills] = useState([]);
  const [activeId, setActiveId] = useState('');
  const [query, setQuery] = useState('');
  const [params, setParams] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/api/skills`)
      .then((res) => readApiJson(res, '技能列表加载失败'))
      .then((data) => {
        setSkills(data.skills || []);
        if (data.skills?.[0]) setActiveId(data.skills[0].id);
      })
      .catch((error) => setLoadError(error.message));
  }, []);

  const activeSkill = skills.find((skill) => skill.id === activeId);
  const grouped = useMemo(() => groupSkills(skills), [skills]);

  useEffect(() => {
    if (!activeSkill) return;
    const nextParams = {};
    activeSkill.controls?.forEach((control) => {
      if (control.type === 'select') nextParams[control.id] = control.options?.[0] || '';
      if (control.type === 'boolean') nextParams[control.id] = false;
      if (control.type === 'text') nextParams[control.id] = '';
    });
    setParams(nextParams);
    setQuery(activeSkill.examples?.[0] || '');
    setResult(null);
  }, [activeId]);

  async function submitRun(event) {
    event.preventDefault();
    if (!activeSkill || !query.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skillId: activeSkill.id, query: query.trim(), params })
      });
      const data = await readApiJson(response, '执行失败');
      setResult(data);
    } catch (error) {
      setResult({ ok: false, message: error.message, content: '' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Settings2 size={18} />
          <span>金融技能控制台</span>
        </div>
        <div className="skill-search">
          <Search size={15} />
          <span>{skills.length} 个本地技能</span>
        </div>
        {Object.entries(grouped).map(([group, items]) => (
          <section className="skill-group" key={group}>
            <h2>{group}</h2>
            {items.map((skill) => (
              <button
                className={`skill-item ${skill.id === activeId ? 'active' : ''}`}
                key={skill.id}
                onClick={() => setActiveId(skill.id)}
              >
                <strong>{skill.title}</strong>
                <span>{skill.outputType}</span>
              </button>
            ))}
          </section>
        ))}
      </aside>

      <section className="workspace">
        {loadError ? (
          <div className="notice error"><AlertCircle size={18} />{loadError}</div>
        ) : null}
        <form className="run-panel" onSubmit={submitRun}>
          <div className="panel-head">
            <div>
              <h1>{activeSkill?.title || '加载中'}</h1>
              <p>{activeSkill?.description || '正在读取本地技能注册表'}</p>
            </div>
            <button className="run-button" disabled={loading || !query.trim()} type="submit">
              {loading ? <Loader2 className="spin" size={17} /> : <Play size={17} />}
              <span>{loading ? '执行中' : '运行'}</span>
            </button>
          </div>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="输入自然语言查询"
            rows={6}
          />
          <SkillControls skill={activeSkill} params={params} setParams={setParams} />
          {activeSkill?.examples?.length ? (
            <div className="examples">
              {activeSkill.examples.map((example) => (
                <button type="button" key={example} onClick={() => setQuery(example)}>
                  {example}
                </button>
              ))}
            </div>
          ) : null}
        </form>

        <div className="result-grid">
          <section className="result-panel">
            <div className="section-title">
              <FileText size={17} />
              <span>结果</span>
            </div>
            {result?.ok === false ? (
              <div className="notice error"><AlertCircle size={18} />{result.message || '执行失败'}</div>
            ) : null}
            <MarkdownView content={result?.content || (loading ? '正在同步执行脚本，请等待结果返回。' : '选择技能并运行后，结果会显示在这里。')} />
          </section>

          <aside className="artifact-panel">
            <div className="section-title">
              <Download size={17} />
              <span>文件与链接</span>
            </div>
            {result?.files?.length ? (
              <div className="artifact-list">
                {result.files.map((file) => (
                  <a key={file.path} href={`${API_BASE}/api/files?path=${encodeURIComponent(file.path)}`}>
                    <Download size={15} />
                    <span>{file.name}</span>
                  </a>
                ))}
              </div>
            ) : (
              <p className="empty">暂无生成文件</p>
            )}
            {result?.links?.length ? (
              <div className="links">
                {result.links.map((link) => (
                  <a key={link.url} href={link.url} target="_blank" rel="noreferrer">
                    {link.url}
                  </a>
                ))}
              </div>
            ) : null}
          </aside>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
