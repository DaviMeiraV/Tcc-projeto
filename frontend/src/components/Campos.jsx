export function Campo({ rotulo, obrigatorio, erro, ajuda, unidade, children }) {
  return (
    <div className={`campo ${erro ? 'invalido' : ''}`}>
      {rotulo && (
        <label className="rotulo">
          {rotulo} {obrigatorio && <span className="obrigatorio">*</span>}
        </label>
      )}
      {unidade ? (
        <div className="com-unidade">
          {children}
          <span>{unidade}</span>
        </div>
      ) : (
        children
      )}
      {(erro || ajuda) && <div className={`dica ${erro ? 'erro' : ''}`}>{erro || ajuda}</div>}
    </div>
  )
}

export function Chips({ opcoes, valor, onChange }) {
  return (
    <div className="chips">
      {opcoes.map((o) => (
        <button
          key={o.valor}
          type="button"
          className={`chip ${valor === o.valor ? 'ativo' : ''}`}
          onClick={() => onChange(o.valor)}
        >
          {o.rotulo}
        </button>
      ))}
    </div>
  )
}

export function ChipsSimNao({ valor, onChange }) {
  return (
    <Chips
      opcoes={[
        { valor: true, rotulo: 'Sim' },
        { valor: false, rotulo: 'Não' },
      ]}
      valor={valor}
      onChange={onChange}
    />
  )
}

export function PerguntaSlider({ titulo, escala, valor, onChange }) {
  return (
    <div className="pergunta">
      <div className="texto">
        <strong>{titulo}</strong>
        <small>{escala}</small>
      </div>
      <div className="controle">
        <input type="range" min="0" max="10" step="1" value={valor} onChange={(e) => onChange(Number(e.target.value))} />
        <div className="valor">{valor} / 10</div>
      </div>
    </div>
  )
}
