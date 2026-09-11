import { Link } from 'react-router-dom'

export default function Concluido() {
  return (
    <div className="pagina">
      <div className="cartao centralizado">
        <h1>Formulário concluído</h1>
        <p>Obrigado pela participação.</p>
        <p>Seus dados foram recebidos e registrados com sucesso.</p>
        <div style={{ marginTop: 26 }}>
          <Link to="/formulario" className="btn primario" style={{ textDecoration: 'none' }}>
            Preencher novamente
          </Link>
        </div>
      </div>
    </div>
  )
}
