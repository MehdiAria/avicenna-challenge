# Notes

## 1. Modeling the channels

I went with two separate models — `EmailChannel` and `SMSChannel` — each with a `OneToOneField` back to `Notification`. The alternative was a single polymorphic `Channel` model with a type field and nullable columns, but that felt like the wrong trade-off: the two channels genuinely don't share a schema (email has `title`/`body`, SMS has `text`), and their status enums are different. Keeping them separate means no nulls for fields that don't apply, and the status choices are enforced at the DB level per channel type.

`OneToOne` rather than `ForeignKey` reflects the domain rule that a notification carries at most one email and one SMS. It also lets Django cache the related object on `prefetch_related`, which matters for the list endpoint.

Each channel has a `tracking_id` (unique, indexed) — this is the opaque ID the provider returns on send, and the field state reports reference. The index is the reason lookups on ingest are O(1) regardless of table size.

## 2. Ingesting state reports

The endpoint accepts a list of reports. A few things it has to deal with that the sample data makes obvious:

- **Out-of-order delivery**: the `sent` event for `em_a1f0c97d2b3e` arrives after `delivered`. I use `occurred_at` (when the event happened at the provider) rather than `received_at` (when we got the report) to decide which status wins. Each channel stores the `occurred_at` of the event that last set its status, and an incoming report only wins if its `occurred_at` is strictly later.

- **Duplicates**: the sample has two identical `delivered` reports for the same tracking ID and timestamp. The `occurred_at` check handles this — equal timestamps don't win, so the second one is a no-op.

- **Unknown tracking IDs**: `sm_3a00b1c2unkn` doesn't exist in our DB. Silently skip — we can't do anything useful with it, and crashing or returning an error would poison a whole batch.

- **Wrong-channel statuses**: `opened` is an email state but appears on an SMS tracking ID in the sample. Skip it — the provider is untrustworthy, and accepting garbage status values would corrupt the channel's state.

The endpoint returns `{"updated": n, "skipped": n}` so callers can tell whether their reports landed.

## 3. Status aggregation

For a notification with both email and SMS, I pick the **best outcome across all channels**. The priority order is: `opened` > `delivered` > `sent` > terminal failures (`bounced` / `failed` / `undelivered`).

The reasoning: if the email was opened but the SMS was undelivered, the message got through — the user saw it. Surfacing `undelivered` as the overall status would be misleading. The notification's job was to reach the user, and it did.

The flip side: if every channel failed, the overall status reflects that. If one is still in-flight (`sent`) and the other failed, the result is `sent` — which is technically optimistic, but accurate: we don't know yet whether that channel will deliver.

## 4. Handling high load

A few things that matter at "thousands of reports per second":

- **Index on `tracking_id`**: every ingest report hits exactly one indexed lookup. No table scans.
- **`update_fields`**: the `save()` call only writes the two changed columns, not the whole row.
- **Batch input**: the endpoint takes a list, so clients can send bulk payloads and reduce HTTP overhead.

What I'd change at real scale:

- **Don't write synchronously in the request**: at high volume the DB becomes the bottleneck fast. The better pattern is to push incoming reports onto a queue (Kafka, SQS) and process them with workers. The HTTP endpoint just acknowledges receipt.
- **Upsert instead of select-then-update**: replace the `get` + `save` with a single `UPDATE ... WHERE tracking_id = ? AND occurred_at < ?` — one round-trip instead of two, and it handles concurrent writes correctly without a race condition.
- **Partitioning**: once the channel tables grow large, partition by `tracking_id` hash or by time range so lookups stay fast without relying solely on the index.