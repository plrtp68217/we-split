# Шпаргалка: `mapped_column()` в SQLAlchemy 2.1

```python
mapped_column([name], [type], *args, **params)
```

## Позиционные

| Аргумент | Значение | Пример |
|---|---|---|
| name | `str` | `"user_login"` |
| type | `TypeEngine` | `String(50)`, `Integer` |
| `*args` | `ForeignKey`, `Sequence`, `Identity`, `Computed`, `CheckConstraint` | `ForeignKey("user.id")` |

## Колонка

| Параметр | Значение |
|---|---|
| `primary_key` | `bool` |
| `nullable` | `bool` (по умолчанию из `Optional[...]`) |
| `name` / `type_` | `str` / `TypeEngine` |
| `autoincrement` | `bool`, `"auto"`, `"ignore_fk"` |
| `index` / `unique` | `bool` |
| `key` | `str` (ключ в `Table.c`) |
| `comment` / `doc` | `str` |
| `quote` | `bool \| None` |
| `system` | `bool` |
| `info` | `dict` |
| `sort_order` | `int` |
| `use_existing_column` | `bool` |

## Значения по умолчанию

| Параметр | Значение |
|---|---|
| `insert_default` | скаляр, callable, `func.now()` |
| `onupdate` | скаляр, callable, SQL-выражение |
| `server_default` | `str`, `text(...)`, `FetchedValue` |
| `server_onupdate` | `FetchedValue`, `Computed` |
| `default` | значение (без dataclass = `insert_default`) |

## ORM-загрузка

| Параметр | Значение |
|---|---|
| `deferred` | `bool` |
| `deferred_group` | `str` |
| `deferred_raiseload` | `bool` |
| `active_history` | `bool` |

## Dataclasses

| Параметр | Значение |
|---|---|
| `init` / `repr` / `compare` / `kw_only` | `bool` |
| `hash` | `bool \| None` |
| `default` | значение |
| `default_factory` | callable |
| `dataclass_metadata` | `Mapping` (новое в 2.1) |

## Прочее

`**kw` — диалект-специфичные аргументы: `postgresql_*`, `mysql_*` и т.п.

## Пример

```python
id: Mapped[int] = mapped_column(primary_key=True)
login: Mapped[str] = mapped_column(String(50), unique=True, index=True)
bio: Mapped[Optional[str]] = mapped_column(deferred=True)
status: Mapped[str] = mapped_column(server_default=text("'active'"))
created_at: Mapped[datetime] = mapped_column(insert_default=func.now())
team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("team.id"))
```