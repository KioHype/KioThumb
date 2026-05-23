# KioThumb — Gerador de Thumbnails para Longplay

**Gera automaticamente várias thumbnails numeradas para canais de longplay no YouTube.** Você escolhe a imagem, posiciona o número do episódio e a logo do jogo onde quiser, e o programa exporta tudo em lote no formato ideal para o YouTube (1280×720).

---

## Por que esse programa existe?

Eu tenho um canal de longplay no YouTube e toda vez que ia postar uma série nova, precisava abrir o Photoshop, criar a thumbnail, salvar, mudar o número, salvar de novo... para cada episódio. Uma encheção de saco!

O **KioThumb** resolve isso: você configura uma vez e manda gerar 10, 20, 50 thumbnails de uma vez. Cada uma com o número certo, a logo do jogo e a imagem que você escolheu.

---

## O que ele faz

- Gera thumbnails numeradas em lote (`#1`, `#2`, `#3`... ou o prefixo que você quiser)
- Preview em tempo real: o que você vê é exatamente o que vai sair
- Arraste o número e a logo direto na tela para posicionar
- Zoom e pan na imagem de fundo para enquadrar do jeito que quiser
- Suporte a múltiplas imagens (cada episódio com uma imagem diferente)
- Importação de fontes personalizadas (.ttf / .otf)
- Logo do jogo em PNG com transparência
- Exporta em JPEG no tamanho padrão do YouTube (1280×720)

---

## 📥 Download

Vá em [Releases](../../releases) e baixe o arquivo `KioThumb.exe`.

Não precisa instalar nada. Basta colocar o `KioThumb.exe` e o `icone.png` na mesma pasta e executar.

> **Sistema operacional:** Windows 10 ou superior  
> **Testado em:** Windows 11

---

## Rodar pelo código-fonte

Se preferir rodar direto pelo Python:

**Requisitos:**
- Python 3.10 ou superior
- Pillow
- psutil

**Instalação das dependências:**
```bash
py -m pip install pillow psutil
```

**Executar:**
```bash
py kiothumb.py
```

> O arquivo `icone.png` precisa estar na mesma pasta que o `kiothumb.py`.

---

## 📁 Estrutura do projeto

```
KioThumb/
├── kiothumb.py       # Código principal
├── icone.png         # Ícone do programa
└── README.md         # Este arquivo
```

---

## Como usar

1. Abra o **KioThumb**
2. Clique em **+ Adicionar** para adicionar uma ou mais imagens
3. No painel do meio, **arraste** a imagem para enquadrar, use o **scroll** para dar zoom
4. **Clique** no número `#1` para selecioná-lo (contorno vermelho) e arraste para posicionar
5. Configure fonte, tamanho, cor e contorno no painel direito
6. Se quiser, adicione a logo do jogo e posicione da mesma forma
7. Lá embaixo, defina a quantidade de thumbnails e clique em **▶ GERAR THUMBNAILS**

---

## Observações

- Se você adicionar **1 imagem** e pedir **10 thumbnails**, a mesma imagem será usada nas 10
- Se você adicionar **4 imagens** e pedir **6 thumbnails**, as imagens 1–4 são usadas nas primeiras 4, e a imagem #4 é repetida nas restantes (o programa avisa antes de gerar)
- As thumbnails são salvas em JPEG com qualidade 92, no tamanho 1280×720 (padrão YouTube)

---

## Autor

Feito por **Daniel Perin**  
Canal: [https://www.youtube.com/@KioHype]

---

## Licença

MIT — use, modifique e distribua à vontade.
