import { useState, useRef, useEffect } from 'react'
import { flushSync } from 'react-dom'
import styles from './App.module.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function renderText(text) {
  return text.split(/\*\*(.*?)\*\*/g).map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    const history = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }))

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '', sources: [] },
    ])

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...history, { role: 'user', content: text }],
        }),
      })

      if (!res.ok) {
        const msg = res.status === 429
          ? 'Limite de requêtes atteinte. Réessayez dans quelques instants.'
          : `Erreur serveur (${res.status}).`
        setMessages(prev => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'error', content: msg, sources: [] }
          return copy
        })
        setLoading(false)
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (!raw) continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'token') {
            flushSync(() => {
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = {
                  ...copy[copy.length - 1],
                  content: copy[copy.length - 1].content + event.content,
                }
                return copy
              })
            })
          } else if (event.type === 'sources') {
            setMessages(prev => {
              const copy = [...prev]
              copy[copy.length - 1] = {
                ...copy[copy.length - 1],
                sources: event.sources,
              }
              return copy
            })
          } else if (event.type === 'error') {
            setMessages(prev => {
              const copy = [...prev]
              copy[copy.length - 1] = {
                role: 'error',
                content: event.message || 'Une erreur est survenue.',
                sources: [],
              }
              return copy
            })
          }
        }
      }
    } catch {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = {
          role: 'error',
          content: 'Impossible de contacter le serveur.',
          sources: [],
        }
        return copy
      })
    }

    setLoading(false)
  }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        Géopolitique du Moyen-Orient
      </header>

      <div className={styles.messages}>
        {messages.map((msg, i) => {
          const isWaiting = loading && i === messages.length - 1 && msg.role === 'assistant' && !msg.content
          return (
            <div key={i} className={`${styles.message} ${styles[msg.role]}`}>
              {isWaiting
                ? <span className={styles.waiting}>En train de réfléchir…</span>
                : renderText(msg.content)
              }
              {msg.sources && msg.sources.length > 0 && (
                <div className={styles.sources}>
                  <span className={styles.sourcesLabel}>Sources ({msg.sources.length})</span>
                  {msg.sources.map((src, j) => (
                    <div key={j} className={styles.sourceCard}>
                      <div className={styles.sourceTitle}>
                        {src.url
                          ? <a href={src.url} target="_blank" rel="noopener noreferrer">{src.title}</a>
                          : src.title
                        }
                      </div>
                      {src.excerpt && (
                        <div className={styles.sourceExcerpt}>{src.excerpt}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputArea}>
        <input
          className={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Posez votre question…"
          autoFocus
          disabled={loading}
        />
        <button className={styles.button} onClick={sendMessage} disabled={loading}>
          Envoyer
        </button>
      </div>
    </div>
  )
}

export default App
