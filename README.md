# 🛠️ Blackwall Cyberpunk Voxel Live Wallpaper — Status & Roadmap

Este documento serve como **ponto de restauração e alinhamento de contexto** para o desenvolvimento do Live Wallpaper animado e interativo no estilo **Cyberpunk Blackwall**.

---

## 📌 Contexto & Objetivos Principais
Criar um papel de parede animado, dinâmico e de alta performance para Windows usando **Python (PyQt6/WebEngine)** como backend de monitoramento/janela e **HTML5 Canvas / JS** como motor de renderização 3D procedimental.

---

## 🚀 O Que Foi Concluído e Estabilizado (Progresso Atual)

### 1. **Arquitetura de Wallpaper Real (Windows Native Integration)**
* **Injeção em Camada Profunda (`WorkerW / Progman`)**: A janela do PyQt6 não é mais uma aplicação flutuante nem um screensaver. Ela é injetada na camada `WorkerW` por chamadas `ctypes` (Win32 API), ficando presa atrás dos ícones da área de trabalho.
* **Interatividade Preservada**: Suporte a clique transparente (`pointer-events: none` global com exceção da UI HUD).
* **Controle da Bandeja (System Tray)**:
  * Ícone na barra de tarefas/bandeja do Windows.
  * Opção manual de **"Próxima Imagem ➔"**.
  * Opção de encerramento limpo do processo.
  * Atalho universal `ESC` na janela para fechamento rápido.

### 2. **Motor 3D Voxel (HTML5 Canvas)**
* **Enquadramento Proporcional e Ajuste de Resolução**: Mapeamento inteligente que redimensiona a imagem para caber inteira na tela (`aspect-ratio: contain`), eliminando o zoom excessivo e cortes indesejados.
* **Projeção 3D com Relevo (Z-Depth)**: Reconstrução volumétrica das imagens baseada na luminância dos pixels (partes mais claras saltam em Z).
* **Matriz de Densidade HD**: Redução no tamanho dos blocos de voxels e passo de renderização ajustado para renderizar traços faciais e detalhes finos com clareza.
* **Efeitos Visuais Cyberpunk**:
  * Paleta de cores focada em **Vermelho Blackwall (`#ff003c`), Magenta, Ciano Neon e Branco Glitch**.
  * Camada de Scanlines e Glitch visual acionada em transições.
  * Parallax sutil reativo ao movimento do mouse.

### 3. **Interface HUD Cyberpunk (UI)**
* **Painel Centralizado estilo Cyber-Deck**:
  * **Relógio e Data** com sincronização em tempo real.
  * **Métricas do Sistema**: Leitura em tempo real de uso de **CPU** e **RAM** via `psutil`.
  * **Audio Feed Input (HUD Mídia)**: Interface pronta para exibição de Faixa/Artista.

---

## 🛠️ Desafios Conhecidos & Status do Music Player

* **Desafio Atual**: A detecção de mídia via consulta de títulos de janelas/processos ainda pode oscilar dependendo do estado do navegador (se a aba do YouTube Music está focada/rodando em segundo plano) ou do executável do Spotify.
* **Tentativa com `winsdk`**: Descartada devido à falha de compilação C++ / MSVC na máquina do usuário.
* **Solução Atual em Teste**: Leitura via chamada nativa do PowerShell acoplada à varredura de processos em segundo plano pelo `psutil`.

---

## 🎯 Próximos Passos & Pontos de Melhoria (Roadmap)

Quando retomar o projeto, o foco recomendado deve ser:

### 1. **Aprimoramento Definitivo do Leitor de Mídia (Media Session)**
* **Abordagem Nativa via Ctypes/WinRT sem DLLs externas**: Implementar um leitor assíncrono via `Windows.Media.Control` diretamente no Python sem passar pelo sub-processo estático do PowerShell para evitar quedas de FPS/delay.
* **Fallback por Audio Session**: Consultar os picos da placa de som (CoreAudio Windows API) para fazer os voxels reagirem ao ritmo real do som de forma suave e opcional.

### 2. **Refinamento do Motor de Renderização Voxel**
* **Otimização de Performance (Offscreen Canvas / WebGL)**: Se a densidade de voxels causar aumento de uso da CPU, migrar a renderização do Canvas 2D para Shader WebGL (Three.js minimalista ou Shaders puros em GLSL).
* **Filtros de Iluminação Rim Light**: Adicionar um brilho nas bordas dos voxels para dar ainda mais sensação de profundidade e contraste nas áreas escuras das imagens.

### 3. **Gerenciamento de Imagens e Configurações**
* **Painel de Configurações Rápido na Bandeja**:
  * Controle de velocidade da troca automática de imagens (ex: 30s, 1min, 5min).
  * Seletor de intensidade de profundidade Z-Depth (relevo do Voxel).
  * Toggle para ativar/desativar o HUD central.

---

## 📂 Estrutura de Arquivos Atual
```
Live wallpaper/
├── launcher.py        # Backend PyQt6 + Injeção na área de trabalho + Monitoramento do Sistema/Mídia
├── index.html         # Frontend HTML5 + CSS HUD + Motor Voxel 3D (Canvas JS)
└── images/            # Diretório de fotos/artes do usuário (.png, .jpg, .webp)
```

---

*Backup criado com sucesso. Bom descanso e até a próxima sessão de código!*