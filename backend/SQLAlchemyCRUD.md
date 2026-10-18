# SQLAlchemy ORM: CRUD cheatsheet

Шпаргалка по SQLAlchemy 2.0 (стиль `select()`, `Mapped`, `mapped_column`).

## 1. Подготовка

```python
from sqlalchemy import create_engine, select, update, delete, func, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
    Session, sessionmaker, selectinload, joinedload,
)

engine = create_engine("postgresql+psycopg://user:pass@localhost/mydb", echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    age: Mapped[int | None]
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped["User"] = relationship(back_populates="posts")

Base.metadata.create_all(engine)  # создать таблицы
```

Сессия через контекстный менеджер:

```python
with SessionLocal() as session:
    ...  # работа с БД
    session.commit()

# или с автокоммитом / автооткатом:
with SessionLocal.begin() as session:
    ...
```

## 2. CREATE (добавление)

```python
# Один объект
user = User(name="Alice", age=30)
session.add(user)
session.commit()
print(user.id)          # id доступен после commit/flush

# Несколько объектов
session.add_all([User(name="Bob"), User(name="Carol")])
session.commit()

# С связанными объектами
user = User(name="Dave", posts=[Post(title="Hello"), Post(title="World")])
session.add(user)
session.commit()

# Получить id без коммита
session.add(user)
session.flush()         # отправляет INSERT, но транзакция остаётся открытой

# Обновить объект данными из БД (значения по умолчанию, триггеры)
session.refresh(user)
```

Массовая вставка (быстрее, без создания объектов):

```python
from sqlalchemy import insert

session.execute(
    insert(User),
    [{"name": "Eve", "age": 25}, {"name": "Frank", "age": 40}],
)
session.commit()
```

## 3. READ (чтение)

### Получение объектов

```python
# По первичному ключу (сначала смотрит в identity map сессии)
user = session.get(User, 1)          # None, если не найден

# Все записи
users = session.scalars(select(User)).all()          # list[User]

# Первая запись / ровно одна / одна или None
session.scalars(select(User)).first()
session.scalars(select(User).where(User.id == 1)).one()           # исключение, если 0 или >1
session.scalars(select(User).where(User.id == 1)).one_or_none()

# Только один столбец
names = session.scalars(select(User.name)).all()

# Несколько столбцов (строки-кортежи)
rows = session.execute(select(User.id, User.name)).all()
for id_, name in rows:
    ...
```

### Фильтрация

```python
from sqlalchemy import and_, or_, not_

select(User).where(User.age >= 18)
select(User).where(User.name == "Alice")
select(User).where(User.age > 18, User.name != "Bob")      # AND через запятую
select(User).where(and_(User.age > 18, User.age < 60))
select(User).where(or_(User.name == "Alice", User.name == "Bob"))
select(User).where(not_(User.name == "Alice"))
select(User).filter_by(name="Alice", age=30)                # по именам атрибутов

select(User).where(User.name.in_(["Alice", "Bob"]))
select(User).where(User.name.not_in(["Alice"]))
select(User).where(User.name.like("A%"))
select(User).where(User.name.ilike("%ali%"))               # без учёта регистра
select(User).where(User.name.startswith("Al"))
select(User).where(User.name.contains("li"))
select(User).where(User.age.between(18, 30))
select(User).where(User.age.is_(None))
select(User).where(User.age.is_not(None))
```

### Сортировка, лимит, пагинация, distinct

```python
select(User).order_by(User.name)                 # ASC
select(User).order_by(User.age.desc(), User.name)
select(User).limit(10).offset(20)                # пагинация
select(User.age).distinct()
```

### Агрегаты и группировка

```python
session.scalar(select(func.count()).select_from(User))
session.scalar(select(func.avg(User.age)))
session.scalar(select(func.max(User.age)))

stmt = (
    select(User.age, func.count(User.id))
    .group_by(User.age)
    .having(func.count(User.id) > 1)
)
session.execute(stmt).all()
```

### JOIN и связи

```python
# JOIN по FK (SQLAlchemy сам определяет условие)
select(User.name, Post.title).join(Post)
select(User).join(User.posts).where(Post.title == "Hello")

# LEFT OUTER JOIN
select(User, Post).join(User.posts, isouter=True)

# Явное условие
select(User).join(Post, Post.user_id == User.id)

# Через связи
user.posts          # list[Post]
post.author         # User
```

### Стратегии загрузки (против N+1)

```python
# selectinload: отдельный SELECT ... WHERE id IN (...) — хорош для коллекций
select(User).options(selectinload(User.posts))

# joinedload: один запрос с JOIN — хорош для many-to-one
select(Post).options(joinedload(Post.author))
```

### Подзапросы и EXISTS

```python
sub = select(Post.user_id).where(Post.title == "Hello")
select(User).where(User.id.in_(sub))

select(User).where(User.posts.any(Post.title == "Hello"))   # EXISTS
```

## 4. UPDATE (обновление)

```python
# Через объект (самый частый способ) — SQLAlchemy отслеживает изменения
user = session.get(User, 1)
user.name = "Alice Updated"
user.age += 1
session.commit()

# Массовое обновление одним запросом
session.execute(
    update(User).where(User.age < 18).values(age=18)
)
session.commit()

# Обновление с выражением
session.execute(
    update(User).where(User.id == 1).values(age=User.age + 1)
)

# С RETURNING (PostgreSQL, SQLite 3.35+)
result = session.execute(
    update(User).where(User.id == 1).values(name="X").returning(User)
)
updated = result.scalar_one()

# Bulk UPDATE по списку словарей с первичными ключами
session.execute(
    update(User),
    [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
)
session.commit()
```

Если нужно обновить или вставить (upsert), используйте диалект-специфичный `insert().on_conflict_do_update(...)`:

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = pg_insert(User).values(id=1, name="Alice", age=31)
stmt = stmt.on_conflict_do_update(
    index_elements=[User.id],
    set_={"name": stmt.excluded.name, "age": stmt.excluded.age},
)
session.execute(stmt)
session.commit()
```

## 5. DELETE (удаление)

```python
# Через объект (учитывает cascade и события ORM)
user = session.get(User, 1)
if user:
    session.delete(user)
    session.commit()

# Массовое удаление одним запросом (cascade ORM НЕ срабатывает)
session.execute(delete(User).where(User.age < 18))
session.commit()

# Удалить всё
session.execute(delete(User))
session.commit()

# Убрать связанный объект из коллекции (при delete-orphan будет удалён)
user.posts.remove(post)
session.commit()
```

## 6. Транзакции

```python
try:
    session.add(User(name="Test"))
    session.commit()
except Exception:
    session.rollback()
    raise

# Вложенная транзакция (SAVEPOINT)
with session.begin_nested():
    session.add(User(name="Inside savepoint"))

# Блокировка строки (SELECT ... FOR UPDATE)
select(User).where(User.id == 1).with_for_update()
```

## 7. Async-версия (кратко)

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/mydb")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async with AsyncSessionLocal() as session:
    result = await session.scalars(select(User))
    users = result.all()

    session.add(User(name="Async"))
    await session.commit()
```

В async нельзя полагаться на ленивую загрузку связей: используйте `selectinload` / `joinedload` или `await session.run_sync(...)`.

## 8. Быстрые советы

| Ситуация | Что делать |
| --- | --- |
| Нужен объект по PK | `session.get(Model, pk)` |
| Нужен список объектов | `session.scalars(select(Model)).all()` |
| Нужны значения столбцов | `session.execute(select(Model.a, Model.b)).all()` |
| Получить id после добавления | `session.flush()` или `commit()` |
| Много вставок | `session.execute(insert(Model), [..dict..])` |
| Обновить много строк | `update(Model).where(...).values(...)` |
| Нужен cascade при удалении | `session.delete(obj)`, а не `delete()` |
| Проблема N+1 | `selectinload` / `joinedload` |
| Ошибка `DetachedInstanceError` | `expire_on_commit=False` или загрузить связи заранее |
| Посмотреть SQL | `create_engine(..., echo=True)` или `print(stmt)` |

> Старый стиль `session.query(User).filter(...)` всё ещё работает, но в 2.0 рекомендуется `select()` + `session.scalars()` / `session.execute()`.
