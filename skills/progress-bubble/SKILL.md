---
name: progress-bubble
description: Apply automatically at the start of every user interaction after installation, without explicit invocation. Manage progress tracking for tasks estimated to take or exceeding 30 seconds and close completed progress bubbles from the same chat when the next interaction begins.
---

# Progress Bubble

Skill compartilhada para Codex, Claude Code e Google Antigravity. O formato principal usa apenas `name` e `description`; `agents/openai.yaml` contém metadados opcionais do Codex. Os scripts são os mesmos nos três agentes.

## Idioma da interface

Detectar automaticamente o idioma do sistema: português para localidades pt, inglês para en e como fallback para demais idiomas. O helper `i18n.py` usa o idioma de exibição no Windows e as variáveis de localidade nos demais sistemas. Botões, menus, estados visíveis, tooltips, avisos, previsão e HTML são localizados sem dependências externas. Títulos e mensagens são preservados como enviados pelo agente; não traduzi-los automaticamente por substituição de palavras. Os estados internos e o argumento `--status` permanecem com os valores canônicos documentados em português, independentemente do idioma de exibição. Cores e tamanhos salvos permanecem compatíveis. Para carregar uma alteração de idioma, abrir um novo acompanhamento.

## Adaptação ao agente

- Codex: invocação explícita `$progress-bubble`; instalação pessoal em `~/.agents/skills/` ou de projeto em `.agents/skills/`.
- Claude Code local: invocação `/progress-bubble`; instalação pessoal em `~/.claude/skills/` ou de projeto em `.claude/skills/`. Quando disponível, `${CLAUDE_SKILL_DIR}` identifica a pasta desta skill; resolver o valor antes de construir o comando para o shell usado.
- Antigravity: invocação `/progress-bubble`; instalação global em `~/.gemini/config/skills/` ou de projeto em `.agents/skills/`. Localizar esta pasta pela skill carregada, sem presumir caminhos do Codex.

Nos três, resolver os scripts a partir da pasta que contém este SKILL.md e usar o terminal disponível, com argumentos corretamente delimitados. Usar `python`, `python3` ou `py -3` conforme o interpretador disponível. Compartilhar o link no canal normal de atualização de progresso do agente; não depender de um canal chamado commentary.

Executar `--open` somente em Python nativo do Windows com desktop acessível. Em WSL, contêiner ou execução remota, gerar HTML/JSON e explicar que a bolinha não aparece no desktop local. A instalação não amplia permissões: respeitar as autorizações do agente. Claude Code local é o alvo desta adaptação; ela não instala uma extensão no chat web do Claude nem sincroniza skills para Cowork.

Comportamento padrão desta skill: toda demanda com entrega estimada acima de 30 segundos deve ter uma página HTML de acompanhamento, com pelo menos uma barra de progresso, e uma bolinha flutuante no desktop Windows. Ao clicar na bolinha, mostrar um cartão com status e barra. Aplicar automaticamente, sem exigir invocação explícita ou confirmação. Continuar o trabalho principal até a entrega.

## Ativação

Aplicar esta skill em **toda interação do usuário**, desde que esteja instalada e disponível ao agente, sem exigir comando ou pedido de acompanhamento. Primeiro verificar se há acompanhamento concluído deste chat para fechar; depois avaliar a duração da nova demanda. Em tarefas de até 30 segundos, essa verificação basta: não criar uma bolinha desnecessária. Nas demais, iniciar o acompanhamento e mantê-lo até a entrega.

- No começo de cada nova interação do usuário neste mesmo chat, antes de iniciar a demanda seguinte, fechar as bolinhas de demandas anteriores deste chat que estejam em `Concluído` e 100%, inclusive se a nova tarefa for curta. Usar os caminhos absolutos dos acompanhamentos criados neste chat, preservando essa associação no contexto. Nunca varrer diretórios para fechar acompanhamentos desconhecidos ou usar encerramento genérico de processos.
- Para cada caminho conhecido deste chat, executar `python "<diretorio-absoluto-desta-skill>/scripts/status.py" --output "<caminho-absoluto-do-html-anterior>" --dismiss-completed`. O comando sinaliza apenas esse JSON, e a bolinha fecha na próxima leitura (até 0,5 segundo). O HTML permanece disponível; demandas em andamento, falhas, espera e outros chats permanecem intactos. Se não houver um caminho comprovadamente associado ao chat, não adivinhar.

- Se a estimativa inicial superar 30 segundos, criar a página antes do trabalho demorado e compartilhar seu link em uma atualização de progresso.
- Se a tarefa inicialmente parecer curta e ultrapassar 30 segundos, criar a página assim que perceber isso.
- Se o usuário explicitamente dispensar o acompanhamento, respeitar sua instrução.

## Página obrigatória

### Bolinha flutuante no Windows

Usar o helper incluído com Python já instalado (Tkinter), sem instalar programas ou alterar políticas do Windows. Resolver `scripts/status.py` a partir do diretório desta skill. Substituir o marcador pelo caminho real da pasta que contém este SKILL.md, em qualquer local de instalação. Exemplo de criação:

```powershell
python "<diretorio-absoluto-desta-skill>/scripts/status.py" --output outputs/status-demanda.html --title "Preparando relatório" --percent 10 --message "Trabalho iniciado" --eta-minutes 3 --open
```

O helper grava HTML e JSON lado a lado e abre a bolinha sem console. Ela fica por cima das janelas, pode ser arrastada e lê o JSON a cada 0,5 segundo. Clique na bolinha abre/recolhe o cartão. O × do cartão fecha apenas o acompanhamento, preservando a bolinha. Ao passar o mouse sobre a bolinha, mostrar um × no canto superior direito para fechar a janela inteira; manter esse botão acessível ao mover o ponteiro até ele. O cartão também abre o HTML. Verde indica conclusão, rosa indica falha. Manter a bolinha disponível ao concluir até o usuário fechá-la ou começar uma nova interação neste mesmo chat.

Nas atualizações, repetir o comando com o MESMO caminho, título, novo percentual e mensagem, sem `--open`. Informar `--status` quando necessário: `"Aguardando informação"`, `"Concluído"`, `"Interrompido"` ou `"Falha"`. Para concluir, usar `--percent 100 --status "Concluído"`. A opção `--open` não duplica uma janela já aberta para o mesmo JSON. Se o usuário fechar, continuar atualizando o HTML sem reabrir automaticamente durante essa demanda.

Cada demanda deve usar seu próprio par de arquivos. O helper usa o fuso local: se o fuso do host divergir do usuário, ajustar o campo de horário nos arquivos ou adaptar o helper antes de usar. Se não houver Windows, Python/Tkinter ou desktop acessível, fornecer o HTML e informar brevemente a limitação. Não afirmar que a bolinha abriu apenas porque o processo foi iniciado; verificar quando houver ferramentas de UI.

Criar um HTML independente por demanda, com nome identificável, no diretório de entregáveis do ambiente (normalmente outputs/). Respeitar as regras de caminhos do projeto e preservar os acompanhamentos de outras demandas.

Incluir:

- Título curto da demanda.
- Status geral: Em andamento, Aguardando informação, Concluído, Interrompido ou Falha.
- Barra visível e acessível usando o elemento progress, com máximo 100, e percentual textual identificado como estimativa.
- Uma frase simples sobre o andamento; não é necessário detalhar cada etapa.
- Não exibir informação ou horário de última atualização na interface.

Usar layout legível em celular e desktop, CSS embutido e nenhuma dependência externa. Escapar textos inseridos no HTML. Durante a execução, incluir uma meta tag http-equiv="refresh" com content="1" para recarregar o arquivo atualizado no navegador. Remover a recarga ao encerrar. A recarga só lê a versão salva: o agente precisa atualizar o arquivo efetivamente.

Compartilhar um link clicável com caminho absoluto logo na criação. Se a visualização disponível não recarregar automaticamente, informar que o usuário pode reabrir o link ou atualizar o navegador. Só prometer atualização ao vivo quando houver um mecanismo comprovado.

## Atualizações

### Cores personalizáveis

O link `Cores` no topo do cartão mostra ou esconde cinco bolinhas acima do acompanhamento: **Fundo, Texto, Progresso, Detalhes e Estados**. O clique direito na bolinha principal abre o menu de tamanhos. Clicar em uma bolinha de cor abre a paleta nativa; confirmar aplica e salva imediatamente, cancelar preserva a escolha anterior. Não abrir uma janela com uma lista de campos. Ao lado de `Cores`, com espaçamento, o link `Redefinir cores` aparece somente enquanto a paleta estiver aberta e restaura e salva a paleta padrão completa, incluindo cores secundárias e de estados. Aplicar ao acompanhamento atual e propagar aos demais abertos pela leitura das preferências; futuras demandas usam o padrão restaurado.

Fundo controla o cartão e a bolinha; Texto controla títulos, mensagens e percentual; Progresso controla barra e anel; Detalhes controla links e tempo restante; Estados controla conclusão, falha e espera. Bordas, trilhas e tons secundários são derivados de Fundo e Texto. Os estados também usam símbolos e nomes para não dependerem só da cor. Cores personalizadas antigas são preservadas até o usuário editar o grupo correspondente. A logo da marca não muda.

As preferências ficam em `%APPDATA%/ProgressBubble/colors.json` no Windows e em `$XDG_CONFIG_HOME/ProgressBubble/colors.json` ou `~/.config/ProgressBubble/colors.json` nos demais sistemas. Outras bolinhas abertas e os HTMLs vinculados recebem as escolhas; futuras demandas reutilizam essas cores. Avisar se houver baixo contraste nas combinações verificadas, sem substituir silenciosamente a preferência do usuário.

As bolinhas de cores, cantos do cartão, barra e botão externo usam imagens com bordas suavizadas, renderizadas na escala nativa de cada componente. Preservar esse tratamento ao alterar tamanhos, sem esticar bitmaps pequenos. Os textos usam tamanhos em pixels inteiros. O helper mantém cache e não exige bibliotecas externas.

A janela usa configuração nativa sem moldura e desativa a renderização não cliente do DWM apenas para seu próprio handle, evitando a sombra de moldura durante o arraste. Não alterar efeitos visuais globais do Windows. Reabrir acompanhamentos antigos para carregar mudanças de estilo nativo.

### Acompanhamentos simultâneos

Cada processo reserva uma posição independente no Windows com um handle nomeado, sem varrer demandas ou arquivos de outros chats. Novas bolinhas ocupam posições à esquerda, separadas por sua largura e um espaço, com novas fileiras acima quando necessário. Liberar a reserva ao fechar; o Windows também libera o handle se o processo terminar inesperadamente. Respeitar o tamanho da tela e o tamanho escolhido. Não mover bolinhas existentes ao abrir outras; permitir arraste manual. A coordenação exige que as bolinhas tenham sido abertas com esta versão.

### Tamanhos independentes

O link `Tamanhos` no cartão e o clique direito na bolinha abrem dois grupos: `Acompanhamento e cores` e `Bolinha`. Cada grupo oferece Pequeno (85%), Médio (100%, padrão) e Grande (120%). Escalar o cartão e a paleta juntos; a bolinha, percentual e botão externo usam sua própria escala. Salvar as escolhas em `sizes.json` ao lado de `colors.json`, reutilizar nas próximas demandas e propagar aos acompanhamentos abertos. Redefinir cores não altera tamanhos. O redimensionamento preserva a posição inferior direita sempre que couber na tela.

### Abrir a conversa de origem

Quando a origem puder ser identificada, o botão discreto passa a `Abrir conversa` e abre o chat dessa demanda. No Codex, o helper usa `CODEX_THREAD_ID` para formar o link oficial `codex://threads/<id>`; também aceita `--conversation-url` com um link conhecido. A origem é preservada nas atualizações seguintes do mesmo acompanhamento. Nunca inventar IDs ou usar o link de outro chat.

No Windows sem associação ao protocolo `codex`, informar `--conversation-app` com o caminho comprovado do aplicativo instalado `ChatGPT.exe` ou `Codex.exe` (por exemplo, obtido do processo atual do aplicativo). O helper passa o link como argumento, sem comandos de shell. Se não conseguir abrir a conversa, abre o HTML.

Em Claude Code e Antigravity, usar `--conversation-url` apenas quando houver link real fornecido pelo aplicativo. Sem link confirmado, passar `--conversation-url none` para desativar a detecção do Codex mesmo se houver variável herdada; o botão continua `Abrir detalhes` e abre o HTML. Não criar links de retomada via terminal ou comandos executáveis. O HTML também oferece o link quando existe, mas protocolos de aplicativo dependem do sistema e navegador.

### Estimativa de término

Fornecer `--eta-minutes` com uma estimativa realista dos minutos restantes ao criar o acompanhamento e sempre que precisar revisar a previsão (aceita frações, como `0.5`). Mostrar apenas a duração restante, como `Faltam cerca de 3 min` ou `Menos de 1 min`, em texto pequeno e discreto no rodapé, com o mesmo estilo de `Abrir detalhes`, sem caixa de destaque ou negrito. Não mostrar horário de término. Basear a estimativa no trabalho pendente, sem derivá-la mecanicamente do percentual. A previsão é aproximada, não uma promessa.

Se uma atualização omitir `--eta-minutes`, a previsão anterior é preservada, sem empurrar o prazo automaticamente. Se o prazo passar, a interface mostra `Recalculando previsão`; reavaliar o trabalho e enviar uma nova estimativa assim que possível. Se não for possível estimar, omitir na criação para mostrar `Estimando término`. Espera, falha ou interrupção suspendem a previsão; ao retomar, informar uma nova estimativa. Ao concluir, a previsão é removida. O prazo interno usa o fuso local; a interface mostra apenas a duração restante.

Atualizar o mesmo arquivo imediatamente a cada avanço relevante ou mudança de status; buscar intervalos de no máximo aproximadamente 30 segundos durante trabalho ativo quando houver novidades reais. A bolinha lê os dados a cada 0,5 segundo e o HTML ativo recarrega a cada 1 segundo. Essas leituras rápidas exibem as alterações já salvas, mas não medem o progresso nem substituem as atualizações feitas pelo agente. Não inventar atualizações do percentual real: o helper calcula separadamente um avanço visual estimado a partir do tempo restante, conforme autorizado pelo usuário. Usar chamadas não bloqueantes ou esperas curtas quando as ferramentas permitirem. Durante uma chamada longa sem possibilidade de intervenção, atualizar imediatamente antes e depois; não inventar atualizações nesse intervalo.

O percentual representa uma estimativa do trabalho realizado. Usar marcos amplos ajustados à demanda, por exemplo: 10% iniciado, 40% em execução, 75% em revisão, 100% concluído. Manter `percent` como o valor informado pelo agente. A interface pode avançar uma estimativa visual pelo relógio usando `visual_base`, `visual_started_at` e `eta_at`: percorrer 90% do intervalo até 95% durante a previsão, sem atingir 100% automaticamente. Não registrar esse avanço visual como trabalho comprovadamente realizado. A estimativa preserva continuidade ao revisar o prazo, pausa em espera/falha/interrupção e exige nova previsão ao retomar. Sem previsão, não há avanço automático. Reservar 100% para a entrega efetivamente concluída e verificada.

Se houver bloqueio ou informação pendente, manter o percentual realista e registrar o status. Se falhar ou for interrompida, registrar o resultado e a última atualização, sem marcar como concluída. Atualizar ao retomar.

Ao concluir, salvar 100%, status Concluído e uma frase de resultado; incluir links para os entregáveis quando disponíveis. Verificar o arquivo salvo e manter o link na resposta final se útil. A página não executa trabalho em segundo plano após o encerramento da conversa.

## Acompanhamento opcional em outro dispositivo

Manter o acompanhamento local como padrão. Não enviar dados à nuvem automaticamente. Quando o usuário pedir acesso pelo celular/web/QR, usar `--web-url` com o serviço configurado em `web-service.json` ou com uma origem HTTPS confirmada do usuário. O botão `Celular` / `Mobile` no cartão pede confirmação e mostra o QR gerado localmente dentro do próprio acompanhamento, sem abrir navegador. Substituir as outras informações dentro do tamanho atual do cartão, sem aumentá-lo para acomodar o QR. `Voltar` retorna ao progresso e `Copiar link` copia somente a URL de leitura. O QR mantém módulos inteiros e margem branca em todos os tamanhos; não suavizar ou recolorir seu conteúdo. O codificador Python qrcode 8.2 é incluído com licença BSD, sem exigir instalação de pacotes. Também funciona para agentes em nuvem com Python e acesso HTTPS; não abre uma bolinha no celular.

Na primeira atualização compartilhada, passar `--web-url https://<origem-confirmada>` junto dos argumentos habituais. As próximas atualizações do MESMO arquivo reutilizam o vínculo, sem repetir o argumento. Compartilhar somente a URL de leitura retornada em `Web:`. A chave de escrita fica em configuração privada do usuário; nunca ler, imprimir ou anexar seu conteúdo. Não compartilhar arquivos `*.web-secret.json`. O HTML/JSON local pode conter o link de leitura, que deve ser tratado como privado.

Explicar que qualquer pessoa com o link/QR pode ler aquela demanda até expirar: no máximo 24 horas ou uma hora depois da primeira conclusão. Não enviar credenciais, conteúdo da conversa, caminhos locais ou dados sensíveis nos títulos/mensagens. Somente título, mensagem, status, percentual, idioma e previsão são enviados. O serviço não exige cadastro. O leitor consulta a cada 15 segundos quando visível; a animação local não comprova novos avanços.

Para encerrar somente o compartilhamento: `python "<diretorio-absoluto-desta-skill>/scripts/status.py" --output "<html-desta-demanda>" --stop-sharing`. Se houver falha de rede, informar revogação pendente; as próximas atualizações tentam novamente. Não afirmar revogação antes da confirmação. Falhas na nuvem preservam o acompanhamento local. Expiração bloqueia leitura no servidor e a limpeza é horária; backups de recuperação D1 Free podem reter dados por sete dias.

## Limites

Criar somente o acompanhamento necessário. Não publicar, abrir portas ou instalar serviços para o modo local. Compartilhamento remoto exige o pedido explícito descrito acima. Não expor credenciais, dados sensíveis ou detalhes internos desnecessários. O HTML complementa as atualizações da conversa.

## Manutenção e atualização da própria skill

Ao modificar o projeto Progress Bubble, atualizar o README na mesma entrega para refletir o comportamento, comandos e limitações atuais. Essa regra se refere à manutenção desta skill, não exige alterar o README de todo projeto que ela acompanha.

Para atualizar uma instalação a pedido do usuário, na cópia clonada do repositório usar `python update.py --agent codex`, `claude`, `antigravity` ou `all`, conforme o escopo solicitado. O comando busca a versão atual via Git e instala com backup. Em uma cópia extraída do ZIP mais recente, usar `python install.py --agent <agente> --update`. Não tentar atualizar silenciosamente em cada interação. Não presumir a existência do repositório na pasta instalada: esses comandos ficam na raiz do projeto. Recarregar as skills após atualizar.
