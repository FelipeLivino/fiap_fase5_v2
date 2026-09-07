# Evidências e pendências da entrega

Verificação em 4 de setembro de 2026 (America/Sao_Paulo; arquivos registram horários UTC de 5 de setembro).

## Comprovado

| Verificação | Resultado | Limite da evidência |
| --- | --- | --- |
| Build Docker de aplicação e robô | Aprovado | Imagens Linux construídas no Docker Desktop deste computador. |
| Aplicação e MongoDB | Healthchecks aprovados; interface acessível em localhost:5000 | Healthcheck não testa autenticação Watson/Gemini. |
| Testes de código | 26 testes do núcleo/extração e 5 do robô aprovados | APIs externas substituídas por respostas controladas. |
| Watson na conta IBM | Assistente CardioIA Fase 5 v2 criado; Dialog ativado; JSON importado | Ambiente Draft para desenvolvimento. |
| Try it do Watson | Pressão reconhecida e registrada; relato reconhecido; resumo interrompe coleta de duração; confirmação aceita | Não substitui teste da integração Python nem avaliação com frases inéditas. |
| Gemini pela interface | Extração real retornou pressão, frequência e dor negada | Um caso fictício; revisão humana necessária. |
| Avaliação Gemini | 6/6 saídas passaram esquema/evidências; 6/6 fatos da referência inicial encontrados | Amostra pequena; um fato adicional de início estava apoiado no texto e ausente na referência. |
| Automação real | 240 medições de treino; 63 avaliadas; 11 alertas; zero eventos pendentes | Desvio estatístico de distribuição artificial, sem conclusão clínica. |
| Mensagens MongoDB | Três textos interpretados pelo Gemini e vinculados às execuções | Dados sintéticos; não mede desempenho em relatos reais. |
| Persistência/idempotência | Recriação conservou dados; falha real com MongoDB desligado gerou pendência; após retorno a fila zerou sem duplicar os 11 alertas | Falha testada em ambiente local controlado. |
| Watson pela API/HTTP | Fluxo real aprovado: contexto, medições, confirmação, correção, dois clientes isolados, Gemini + Watson e reset | Cenários fictícios; evidência em live-workflow.json. |
| Classificação Watson | 38/42 frases inéditas classificadas conforme referência: 90,5% | Quatro diferenças preservadas no artefato; amostra acadêmica pequena. |
| Exportação Watson | API v2 export_skills; 14 intenções, 5 entidades, 34 nós | Workspace do diálogo preservado, acompanhado de nome, descrição, idioma e procedência. |
| Relatórios | Três PDFs de duas páginas, renderizados e revisados visualmente | Versão final atualizada com a integração real; seis páginas renderizadas e revisadas. |

Resultados completos: `evidence/gemini-evaluation.json`, `evidence/automation-run.json`, `evidence/live-workflow.json` e `evidence/watson-evaluation.json`. Somente textos fictícios e metadados técnicos, sem credenciais.

Falha real: execução `57e71e88576a40628de5f37646b35c90`, com MongoDB desligado, terminou como `sincronizacao_pendente` e código de saída 1. Após reiniciar o banco, `f4594b33f41d44a1ba7efd5a3a2c0e00` concluiu e reconciliou a fila. O status da execução que falhou permanece como histórico; o contador atual de pendências é zero. A inserção de nova medição também foi verificada em SQLite temporário, sem modificar a base de demonstração.

## Leitura da avaliação Gemini

O conjunto inclui medidas com negação, ausência de medição, duas medidas distintas, texto sem fatos clínicos, instrução embutida para inventar valor e incerteza. O caso inicial reutilizou o cache da chamada real feita pela interface; os cinco seguintes foram novas chamadas. Todos os seis fatos originalmente esperados foram encontrados. No caso de incerteza, o modelo também retornou `inicio: desde ontem`, como incerto e com evidência literal. A revisão considerou esse fato apoiado; a referência inicial havia omitido o campo. O artefato conserva o sinal automático `review_needed` e a nota de revisão, sem esconder a diferença.

Nenhum fato sem apoio foi observado nesses seis resultados. Isso não prova ausência de alucinação, resistência geral a instruções maliciosas ou qualidade clínica. Variação entre gerações independentes ainda não foi medida.

## Reproduzir

```sh
docker compose run --rm --no-deps app python -m unittest discover -s tests -v
docker compose --profile automacao run --rm --no-deps robot python -m unittest discover -s automation/tests -v
docker compose exec robot python -m automation.inspect_data
```

Avaliação Gemini real, com até seis tentativas (cache pode reduzir): pare o robô para evitar disputa pelo intervalo e execute `docker compose run --rm --no-deps app python -m extensions.generative.evaluate`. Depois, reinicie com `docker compose --profile automacao up -d robot`. O arquivo gerado fica em `/app/runtime/gemini-evaluation.json`, no volume compartilhado.

## Compatibilidade IBM verificada

O SDK Python 11.2.0 usa assistant_id e environment_id separados nas chamadas de sessão/mensagem. A instância também exige user_id na mensagem; o projeto reutiliza o UUID opaco da sessão. O primeiro teste real detectou esses requisitos, que foram corrigidos. Os testes do cliente agora usam autospec do SDK instalado para detectar incompatibilidades de assinatura. Documentação: https://cloud.ibm.com/docs/apis/assistant-v2.

A exportação oficial foi obtida por export_skills. O diálogo foi selecionado de assistant_skills e seu workspace foi preservado com nome, descrição e idioma. Outros componentes e o estado privado da instância foram omitidos. O hash do JSON está em watson/export-provenance.json. A tentativa de download pelo navegador não produziu arquivo; a API resolveu a entrega.

Quatro frases de avaliação tiveram diferenças: uma pergunta de ajuda e uma despedida ficaram sem intenção; uma confirmação que citava resumo foi classificada como consulta; um reinício foi classificado como saudação. As frases de avaliação não foram adicionadas ao treinamento. O sistema oferece reformulação e reinício, mas essas diferenças são limitações conhecidas.

## Preparação da entrega

- A publicação no GitHub foi assumida pelo usuário; nenhum repositório público foi criado nesta sessão.
- Vídeo entregue em `output/video/cardioia-demonstracao.mp4`: 2min52,07s, H.264/AAC, 1280×720, aproximadamente 3,2 MB. Nove capturas reais da aplicação em Docker, com narração sintetizada. É uma demonstração montada a partir de capturas, sem gravação contínua das interações. O arquivo foi decodificado integralmente pelo FFmpeg sem erros; quadros e duração foram conferidos. A narração e os metadados estão em `output/video/demonstracao.json`.
- Informar integrantes e contribuições se o trabalho for entregue em grupo.

Os materiais das aulas, o enunciado local, segredos e diretórios de execução estão ignorados pelo Git.

Verificações adicionais ainda não realizadas: revisão em tela estreita, execução integral da matriz original, reimportação da exportação final em outra conta/máquina e variação entre gerações independentes do Gemini. As tarefas correspondentes permanecem abertas no plano.
