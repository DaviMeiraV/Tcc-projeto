# =============================================================================
# MODULO PARADO — NAO ESTA EM USO PELA APLICACAO.
#
# A logica de score do TCC ainda sera definida e validada cientificamente pelo
# autor. Este arquivo fica aqui apenas como rascunho de referencia e NAO e
# importado por nenhuma rota. Pode ser reescrito ou removido livremente.
# =============================================================================

"""Análise das fotografias da prática esportiva.

O objetivo é extrair indicadores posturais simples da imagem enviada, sem depender
de modelo de pose pesado. A silhueta do atleta é isolada do fundo por contraste,
e sobre ela são medidos:

  * inclinação do tronco (eixo principal da massa de pixels do sujeito);
  * simetria esquerda/direita da distribuição de massa;
  * verticalidade do apoio (alinhamento entre o centro de massa superior e a base).

Esses indicadores, combinados com a fase do movimento declarada pelo participante,
geram alertas biomecânicos qualitativos. É uma triagem exploratória para o TCC,
não um laudo clínico.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageOps

TAMANHO_ANALISE = 320


def _silhueta(img: Image.Image) -> np.ndarray:
    """Máscara booleana aproximada do sujeito, por desvio em relação ao fundo."""
    cinza = np.asarray(ImageOps.grayscale(img), dtype=np.float32) / 255.0

    # Gradiente local: o sujeito concentra as bordas; o fundo tende a ser liso.
    gy, gx = np.gradient(cinza)
    bordas = np.sqrt(gx**2 + gy**2)

    # Fundo estimado pelas faixas laterais da imagem.
    largura = cinza.shape[1]
    faixa = max(1, largura // 10)
    fundo = np.concatenate([cinza[:, :faixa].ravel(), cinza[:, -faixa:].ravel()])
    contraste = np.abs(cinza - float(np.median(fundo)))

    escore = contraste + bordas * 2.0
    limiar = float(np.percentile(escore, 82))
    return escore > limiar


def _maior_componente(mask: np.ndarray) -> np.ndarray:
    """Mantém apenas a faixa vertical central de maior densidade (o atleta)."""
    colunas = mask.sum(axis=0).astype(np.float32)
    if colunas.sum() == 0:
        return mask
    # Suavização por média móvel para achar o "corpo" principal.
    janela = max(3, mask.shape[1] // 20)
    kernel = np.ones(janela) / janela
    suave = np.convolve(colunas, kernel, mode="same")
    centro = int(np.argmax(suave))
    limite = float(suave.max()) * 0.25

    esq, dir_ = centro, centro
    while esq > 0 and suave[esq - 1] > limite:
        esq -= 1
    while dir_ < len(suave) - 1 and suave[dir_ + 1] > limite:
        dir_ += 1

    recorte = np.zeros_like(mask)
    recorte[:, esq : dir_ + 1] = mask[:, esq : dir_ + 1]
    return recorte


def analisar_imagem(caminho: str, modalidade: str, fase: str, joelho: str | None) -> dict:
    """Extrai métricas posturais e devolve alertas legíveis."""
    try:
        with Image.open(caminho) as bruta:
            img = ImageOps.exif_transpose(bruta.convert("RGB"))
            img.thumbnail((TAMANHO_ANALISE, TAMANHO_ANALISE))
            mask = _maior_componente(_silhueta(img))
            largura_px, altura_px = img.size
    except Exception as exc:  # imagem corrompida ou formato inesperado
        return {"ok": False, "erro": f"Não foi possível analisar a imagem: {exc}", "alertas": []}

    ys, xs = np.nonzero(mask)
    if len(xs) < 200:
        return {
            "ok": False,
            "erro": "Não foi possível isolar o atleta do fundo. Use uma foto de corpo inteiro, de perfil, com fundo contrastante.",
            "alertas": [],
        }

    cx, cy = float(xs.mean()), float(ys.mean())

    # Eixo principal da silhueta (PCA de 2 dimensões) -> inclinação do tronco.
    coords = np.stack([xs - cx, ys - cy])
    cov = np.cov(coords)
    autovalores, autovetores = np.linalg.eigh(cov)
    principal = autovetores[:, int(np.argmax(autovalores))]
    inclinacao = abs(math.degrees(math.atan2(principal[0], principal[1])))
    if inclinacao > 90:
        inclinacao = 180 - inclinacao

    # Simetria: massa de pixels à esquerda vs. à direita do centro de massa.
    esq = int((xs < cx).sum())
    dir_ = int((xs >= cx).sum())
    simetria = round(min(esq, dir_) / max(esq, dir_) * 100, 1) if max(esq, dir_) else 0.0

    # Alinhamento vertical: deslocamento do tronco em relação à base de apoio.
    metade = cy
    topo = xs[ys < metade]
    base = xs[ys >= metade]
    desvio_base = 0.0
    if len(topo) > 20 and len(base) > 20:
        desvio_base = round(abs(float(topo.mean()) - float(base.mean())) / largura_px * 100, 1)

    # Proporção da imagem ocupada pelo atleta — indica enquadramento adequado.
    ocupacao = round(len(xs) / (largura_px * altura_px) * 100, 1)

    alertas = _alertas(modalidade, fase, joelho, inclinacao, simetria, desvio_base, ocupacao)

    return {
        "ok": True,
        "modalidade": modalidade,
        "fase": fase,
        "joelho_frente": joelho,
        "inclinacao_tronco_graus": round(inclinacao, 1),
        "simetria_percent": simetria,
        "desvio_alinhamento_percent": desvio_base,
        "ocupacao_quadro_percent": ocupacao,
        "alertas": alertas,
        "pontos_risco": sum(a["peso"] for a in alertas),
    }


def _alertas(
    modalidade: str,
    fase: str,
    joelho: str | None,
    inclinacao: float,
    simetria: float,
    desvio: float,
    ocupacao: float,
) -> list[dict]:
    """Traduz as métricas em observações biomecânicas com peso de risco (0-10)."""
    achados: list[dict] = []

    if ocupacao < 4:
        achados.append({
            "titulo": "Enquadramento insuficiente",
            "descricao": "O atleta ocupa pouco espaço na foto, o que reduz a confiabilidade da análise. Refaça a captura mais próximo e de perfil.",
            "peso": 0,
            "nivel": "info",
        })

    if modalidade == "corrida":
        if inclinacao > 22:
            achados.append({
                "titulo": "Inclinação de tronco acentuada",
                "descricao": f"Eixo do tronco a {inclinacao:.0f}° da vertical. Inclinação excessiva desloca a carga para a cadeia posterior e para a região lombar.",
                "peso": 6, "nivel": "alto",
            })
        elif inclinacao > 14:
            achados.append({
                "titulo": "Inclinação de tronco moderada",
                "descricao": f"Eixo do tronco a {inclinacao:.0f}° da vertical. Aceitável, mas vale acompanhar em treinos longos.",
                "peso": 3, "nivel": "medio",
            })
        elif inclinacao < 4:
            achados.append({
                "titulo": "Tronco excessivamente ereto",
                "descricao": "Postura muito vertical tende a aumentar o tempo de contato com o solo e o impacto no joelho.",
                "peso": 3, "nivel": "medio",
            })

        if fase == "contato_inicial" and desvio > 12:
            achados.append({
                "titulo": "Aterrissagem à frente do centro de massa",
                "descricao": "No contato inicial o tronco aparece deslocado em relação à base de apoio, padrão associado a sobrepasso (overstriding) e a maior impacto na tíbia e no joelho.",
                "peso": 7, "nivel": "alto",
            })
        if fase == "apoio_medio" and desvio > 10:
            achados.append({
                "titulo": "Instabilidade no apoio médio",
                "descricao": "Desalinhamento entre tronco e base durante o apoio médio sugere queda pélvica contralateral e sobrecarga no quadril do lado de apoio.",
                "peso": 6, "nivel": "alto",
            })

    else:  # ciclismo
        if inclinacao > 45:
            achados.append({
                "titulo": "Tronco muito baixo sobre o guidão",
                "descricao": f"Ângulo de {inclinacao:.0f}° em relação à vertical. Posição agressiva demais sobrecarrega a lombar e a cervical em pedaladas longas.",
                "peso": 5, "nivel": "medio",
            })
        if fase == "extensao_maxima" and desvio > 14:
            achados.append({
                "titulo": "Extensão máxima com desalinhamento",
                "descricao": "Na extensão máxima o quadril aparece deslocado, o que costuma indicar selim alto demais e balanço pélvico — fator de dor lombar e no joelho posterior.",
                "peso": 6, "nivel": "alto",
            })
        if fase == "fase_superior" and desvio > 14:
            achados.append({
                "titulo": "Fechamento excessivo do quadril",
                "descricao": "Desalinhamento na fase superior da pedalada sugere avanço excessivo do selim, aumentando a compressão femoropatelar.",
                "peso": 5, "nivel": "medio",
            })

    if simetria < 70:
        achados.append({
            "titulo": "Assimetria lateral relevante",
            "descricao": f"A distribuição de massa corporal na imagem é {simetria:.0f}% simétrica. Assimetrias persistentes são um dos preditores mais consistentes de lesão por sobrecarga.",
            "peso": 6, "nivel": "alto",
        })
    elif simetria < 82:
        achados.append({
            "titulo": "Assimetria lateral leve",
            "descricao": f"Simetria de {simetria:.0f}%. Dentro do esperado para uma foto isolada, mas vale reavaliar em vídeo.",
            "peso": 2, "nivel": "medio",
        })

    if joelho and modalidade == "corrida" and not achados:
        achados.append({
            "titulo": f"Padrão sem alterações evidentes ({joelho})",
            "descricao": "Não foram detectados desvios posturais relevantes nesta captura.",
            "peso": 0, "nivel": "ok",
        })

    return achados
