# MongoDB - estrutura documental

Banco `cardioia`, criado pelo primeiro ciclo do robô. Autenticação configurada por variáveis do serviço; nenhuma credencial aparece nos documentos. O `_id` indexado e único é a chave de idempotência.

| Coleção | Identificador | Conteúdo |
| --- | --- | --- |
| `runs` | UUID do ciclo | início, fim, status, quantidade processada, código de erro |
| `events` | `medicao:<id>:<versao>` ou `texto:<id>` | origem, execução, resultado, escore/versão ou modelo, data |
| `messages` | `texto-001` etc. | paciente fictício, texto original, status, extração, execução e atualização |

Exemplo de mensagem antes da interpretação:

```json
{"_id":"texto-001","paciente_id":"SIM-001","text":"Minha frequência foi 72 bpm. Não tenho dor.","status":"pendente"}
```

Após sucesso, `status` passa a `interpretada` e `extraction` recebe fatos com evidências literais. Falhas mantêm a mensagem pendente. O esquema é aplicado pelo código e pelo validador Pydantic da extração; não há validação `$jsonSchema` instalada no servidor.

Eventos SQL pendentes são replicados em `events` e `runs` por substituição/upsert. O robô só marca a entrega após confirmação do MongoDB. Se cair depois do envio, o reenvio usa o mesmo `_id`. Não há transação distribuída entre bancos: a consistência é eventual e observável no contador de pendências.
