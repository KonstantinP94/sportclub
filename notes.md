# SportClub — конспект

**Стек:** Python 3.12, Django 6.1, SQLite, Tailwind, Git.
**Архитектура:** 2 приложения — `users` (аутентификация), `sport` (бизнес-логика). MPA (серверный рендеринг).
**Суперюзер:** `konst9213`

---

## 1. Модели (`sport/models.py`)

**Trainer:** `first_name`, `last_name`, `specialization`, `experience` (валидатор max 70), `photo` (ImageField → нужен Pillow), `description`.

**Slot:** `trainer` (FK, `related_name='slots'`), `date`, `start_time`, `end_time`, `is_booked`.
- `Meta.unique_together = ('trainer','date','start_time')`
- `clean()`: запрет прошедшей даты (только для новых через `not self.pk`) + `start < end`.
- `@property is_past` → `date < today`.

**Booking:** `user` (FK, `related_name='bookings'`), `slot` (**OneToOneField** — 1 слот = 1 бронь), `created_at` (`auto_now_add`).

**Review:** `trainer` (FK, `related_name='reviews'`), `user` (FK, без related_name → `review_set`), `rating` (choices 1–5), `text`, `created_at`.
- `Meta.unique_together = ('trainer','user')`

**Сигналы** (внизу `models.py`):
```python
@receiver(post_save, sender=Booking)   # created=True → slot.is_booked=True
@receiver(post_delete, sender=Booking) # slot.is_booked=False
```
Зачем: синхронизация `is_booked` при создании/удалении через любое место.

**Связи:** `User → Booking → Slot → Trainer → Review`. В `Booking` нет поля `trainer` — доступен через `booking.slot.trainer` (нормализация).

---

## 2. Админка (`sport/admin.py`)

```python
@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display  = ('trainer','date','start_time','end_time','is_booked')  # колонки
    list_filter   = ('trainer','is_booked','date')                          # фильтры справа
    search_fields = ('trainer__first_name','trainer__last_name')            # __ = связь

    def get_readonly_fields(self, request, obj=None):
        if obj: return ('date',)   # при редактировании дата только для чтения
        return ()
```

---

## 3. Views (`sport/views.py`)

**home:**
```python
trainers = Trainer.objects.all()
return render(request, 'home.html', {'trainers': trainers})
```

**trainer_detail:**
```python
trainer = get_object_or_404(Trainer, id=trainer_id)  # 404 если нет
slots = trainer.slots.filter(date__gte=date.today()) # только будущие

date_from = request.GET.get('date_from', '')         # параметры из URL
if date_from: slots = slots.filter(date__gte=date_from)  # >=
if date_to:   slots = slots.filter(date__lte=date_to)    # <=
if show_only_free == 'on': slots = slots.filter(is_booked=False)
slots = slots.order_by('date','start_time')

reviews = trainer.reviews.select_related('user').all()   # JOIN, решает N+1
avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']  # None если нет отзывов
```

---

## 4. Аутентификация (`users/`)

**forms.py:** `CustomUserCreationForm(UserCreationForm)` — пароль хешируется автоматически.

**views.py:**
```python
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user)
            return redirect('sport:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})  # return В КОНЦЕ

def login_view(request):
    form = AuthenticationForm(request, data=request.POST)    # request ПЕРВЫМ
    if form.is_valid():
        login(request, form.get_user()); return redirect('sport:home')

def logout_view(request):
    logout(request); return redirect('users:login')          # users с "s"
```

**urls.py:** `app_name = 'users'` + `urlpatterns` (с "s").
**settings.py:** `LOGIN_URL = 'users:login'`.

**Сессии/куки:** после `login()` Django ставит куку `sessionid` → по ней находит сессию → кладёт `User` в `request.user`.

---

## 5. Шаблоны

- `layout.html` — базовый: шапка, `{% if user.is_authenticated %}`, `{% block content %}`.
- Дочерние: `{% extends 'layout.html' %}` → **имя в кавычках**.
- `{% url 'users:login' %}` — namespace + имя.
- Фильтры: `{{ value|date:"d.m.Y" }}` — **без пробела** после `:`.

---

## 6. Ключевые концепции

| Понятие | Суть |
|---------|------|
| MVT | Model → View → Template |
| ORM | БД через Python-классы |
| `render` | Шаблон + контекст → `HttpResponse` |
| `redirect` | HTTP 302 |
| `get_object_or_404` | Объект или 404 |
| `__gte` / `__lte` | ≥ / ≤ |
| `select_related` | JOIN, решает N+1 |
| `aggregate(Avg())` | SQL AVG |
| `@login_required` | Только авторизованным |
| `?next=` | Возврат после логина |
| CSRF | `{% csrf_token %}` в формах |
| Сигналы | Реакция на события модели |
| `app_name` | Namespace для URL (`sport:home`) |
| `related_name` | Имя обратной связи (`trainer.slots`) |

---

## 7. Частые ошибки

| Ошибка | Правильно |
|--------|-----------|
| `max_lenght` | `max_length` |
| `BoleanField` | `BooleanField` |
| `ForeingKey` | `ForeignKey` |
| `select_releted` | `select_related` |
| `user.authenticated` | `user.is_authenticated` |
| `CustomCreationForm` | `CustomUserCreationForm` |
| `AuthentificationForm` | `AuthenticationForm` |
| `urlpattern` | `urlpatterns` |
| `uniquetogether` | `unique_together` |
| `django.ulrs` | `django.urls` |
| `extends layout.html` | `extends 'layout.html'` |
| `date: "d.m.Y"` | `date:"d.m.Y"` |
| view → `None` | `return render(...)` в конце |
| `on_delete=CASCADE` | `on_delete=models.CASCADE` |

---

## 8. Вопросы для самопроверки

1. `ForeignKey` vs `OneToOneField`?
2. Почему в `Booking` нет поля `trainer`?
3. Зачем `related_name`?
4. Зачем `post_save` проверяет `created`?
5. `@property` зачем нужен?
6. `list_display` vs `list_filter`?
7. Почему `trainer__first_name` в `search_fields`?
8. `get_object_or_404` vs `objects.get`?
9. Почему фильтрация через GET?
10. Что такое N+1 и как `select_related` его решает?
11. Почему `AuthenticationForm(request, data=...)` — `request` первым?
12. Что делает `@login_required` и откуда берёт URL?
13. Что такое `?next=`?
14. Зачем сессии и куки?

---

## 9. Прогресс

- [x] Шаг 1 — окружение, проект, приложения
- [x] Шаг 2 — модели + миграции
- [x] Шаг 3 — админка
- [x] Шаг 4 — views + шаблоны (главная)
- [x] Шаг 5 — trainer_detail + фильтры
- [x] Шаг 6 — аутентификация
- [ ] Шаг 7 — бронирование
- [ ] Шаг 8 — отзывы CRUD
- [ ] Шаг 9 — личный кабинет
- [ ] Шаг 10 — медиа
- [ ] Шаг 11 — финал, презентация

---

## 10. Команды

```bash
venv\Scripts\activate
python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser
python manage.py shell
git add . && git commit -m "..." && git push
```