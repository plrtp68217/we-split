# Шпаргалка: связи между таблицами в SQLAlchemy 2.1

```python
from typing import Optional
from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
```

Два уровня: `ForeignKey` в `mapped_column` создаёт связь в БД, а `relationship()` создаёт связь между Python-объектами.

## One-to-Many / Many-to-One

```python
class Parent(Base):
    __tablename__ = "parent"
    id: Mapped[int] = mapped_column(primary_key=True)
    children: Mapped[list["Child"]] = relationship(back_populates="parent")

class Child(Base):
    __tablename__ = "child"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped["Parent"] = relationship(back_populates="children")
```

Если связь необязательная, используйте `Optional[int]` для FK и `Mapped[Optional["Parent"]]` для объекта.

## One-to-One

Это One-to-Many, у которого со стороны «один» указан скаляр, а не `list`:

```python
class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile: Mapped["Profile"] = relationship(back_populates="user")

class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True)
    user: Mapped["User"] = relationship(back_populates="profile")
```

## Many-to-Many (через таблицу-связку)

```python
post_tag = Table(
    "post_tag", Base.metadata,
    Column("post_id", ForeignKey("post.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)

class Post(Base):
    __tablename__ = "post"
    id: Mapped[int] = mapped_column(primary_key=True)
    tags: Mapped[list["Tag"]] = relationship(secondary=post_tag, back_populates="posts")

class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    posts: Mapped[list["Post"]] = relationship(secondary=post_tag, back_populates="tags")
```

## Many-to-Many с доп. полями (Association Object)

```python
class Enrollment(Base):
    __tablename__ = "enrollment"
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True)
    grade: Mapped[Optional[int]]
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")

class Student(Base):
    __tablename__ = "student"
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")

class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True)
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
```

## Самоссылка (дерево)

```python
class Node(Base):
    __tablename__ = "node"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("node.id"))
    parent: Mapped[Optional["Node"]] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Node"]] = relationship(back_populates="parent")
```

## Несколько FK на одну таблицу

```python
billing_id: Mapped[int] = mapped_column(ForeignKey("address.id"))
shipping_id: Mapped[int] = mapped_column(ForeignKey("address.id"))
billing: Mapped["Address"] = relationship(foreign_keys=[billing_id])
shipping: Mapped["Address"] = relationship(foreign_keys=[shipping_id])
```

## `ForeignKey(...)`: основные параметры

| Параметр | Значения |
|---|---|
| `ondelete` | `"CASCADE"`, `"SET NULL"`, `"RESTRICT"`, `"NO ACTION"`, `"SET DEFAULT"` |
| `onupdate` | то же |
| `name` | имя ограничения (`str`) |

## `relationship(...)`: основные параметры

| Параметр | Значения / назначение |
|---|---|
| `back_populates` | `str`: имя обратного атрибута (явно, с обеих сторон) |
| `backref` | `str`: создаёт обратный атрибут автоматически (устаревший стиль) |
| `secondary` | `Table`: таблица-связка для M2M |
| `foreign_keys` | список колонок, если FK несколько |
| `remote_side` | колонки «удалённой» стороны (самоссылка) |
| `primaryjoin` / `secondaryjoin` | своё условие JOIN (строка или выражение) |
| `uselist` | `bool`, обычно выводится из аннотации |
| `order_by` | колонка или выражение сортировки коллекции |
| `cascade` | `"save-update, merge"` (по умолчанию), `"all, delete-orphan"`, `"all"`, `"delete"` |
| `passive_deletes` | `True`: доверить удаление `ondelete="CASCADE"` в БД |
| `viewonly` | `bool`: связь только для чтения |
| `lazy` | см. ниже |

## `lazy`: стратегии загрузки

| Значение | Поведение |
|---|---|
| `"select"` | по умолчанию, отдельный SELECT при обращении |
| `"selectin"` | SELECT ... IN, лучший выбор для коллекций |
| `"joined"` | LEFT JOIN в основном запросе, хорошо для many-to-one |
| `"subquery"` | через подзапрос |
| `"raise"` / `"raise_on_sql"` | исключение при ленивой загрузке |
| `"noload"` | не загружать |
| `"write_only"` | с аннотацией `WriteOnlyMapped[...]`, для больших коллекций |
| `"dynamic"` | `DynamicMapped[...]`, устаревший вариант |

Стратегию можно задать и в запросе: `select(Parent).options(selectinload(Parent.children))`.

## Типовой каскад «удалять детей вместе с родителем»

```python
children: Mapped[list["Child"]] = relationship(
    back_populates="parent", cascade="all, delete-orphan", passive_deletes=True
)
parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id", ondelete="CASCADE"))
```