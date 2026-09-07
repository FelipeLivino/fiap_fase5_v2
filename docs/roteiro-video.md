# Demonstração entregue

Arquivo: `output/video/cardioia-demonstracao.mp4`. Duração final: **2min52,07s**. Formato MP4 H.264/AAC, 1280×720, 25 fps.

O vídeo usa nove capturas reais da aplicação executada em Docker e narração sintetizada em português (Microsoft Maria Desktop). Não é uma gravação contínua de tela. Os textos são fictícios; credenciais não aparecem. O JSON ao lado do vídeo registra a narração e os tempos aproximados dos segmentos. A execução Docker é comprovada pelos testes e pela documentação de validação; não há imagem de terminal no vídeo.

| Início aproximado | Narração |
| --- | --- |
| 0:00 | Este é o CardioIA, protótipo acadêmico da fase cinco. A aplicação funciona em Docker e integra Watson Assistant, Flask e uma interface HTML. Os dois desafios Ir Além usam Gemini para extrair informações e um robô Python com SQLite, MongoDB e Isolation Forest. Todos os dados desta demonstração são fictícios. |
| 0:24 | Primeiro, solicito o registro da pressão. O Watson reconhece a intenção e pede os dois valores acompanhados da unidade. |
| 0:33 | A medição cento e vinte por oitenta é reconhecida como entidade e aparece no resumo. O contexto fica preservado entre as mensagens, sem transformar a medição em diagnóstico. |
| 0:46 | A confirmação depende de uma mensagem explícita do usuário. O indicador muda para confirmado. Também é possível corrigir informações e iniciar uma nova conversa, com limpeza do contexto anterior. |
| 1:00 | No Ir Além um, o Gemini três ponto cinco Flash Lite extrai dados de um texto fictício. A pressão e a frequência ficam afirmadas; dor fica negada, preservando o sentido do relato. Cada fato traz sua evidência literal. Este resultado veio da API e agora é reutilizado pelo cache, economizando chamadas. |
| 1:23 | O JSON expõe campo, valor, estado e evidência. O backend verifica o esquema e exige que os trechos existam no texto original. Antes de incluir o relato no Watson, o usuário revisa e confirma. Essas verificações não substituem avaliação clínica. |
| 1:41 | Após a revisão, o texto original entra na conversa para nova conferência. As medições já registradas são preservadas. Os fatos extraídos não sobrescrevem automaticamente os campos clínicos. |
| 1:56 | No Ir Além dois, o robô consulta medições no SQLite e aplica Isolation Forest. Neste conjunto sintético, sessenta e três medições foram avaliadas e onze desvios estatísticos foram registrados. Os eventos são sincronizados com o MongoDB. Uma fila persistente permite recuperar falhas sem duplicar alertas. Esses desvios não representam diagnóstico ou classificação de risco clínico. |
| 2:24 | O botão Nova conversa limpa os dados anteriores. A validação incluiu trinta e um testes automatizados, um fluxo completo com APIs reais e quarenta e duas frases inéditas no Watson, com trinta e oito classificações corretas. O código, os comandos Docker, as evidências e os três relatórios acompanham a entrega. Esta demonstração usa capturas reais e narração sintetizada. |

O arquivo passou por decodificação integral sem erros, conferência de duração e revisão visual de quadros. A publicação do vídeo ou seu envio como arquivo fica a cargo do responsável pela entrega.
