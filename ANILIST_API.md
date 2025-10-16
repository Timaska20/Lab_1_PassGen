# AniList GraphQL API Cheatsheet

AniList предоставляет единую GraphQL-точку входа по адресу `https://graphql.anilist.co`. Все запросы выполняются методом `POST`
и используют JSON-тело с полями `query`, а при необходимости — `variables` и `operationName`.

## Базовые настройки для Postman
1. Создайте новый запрос `POST` и укажите URL `https://graphql.anilist.co`.
2. На вкладке **Headers** добавьте пару `Content-Type: application/json`.
3. (Необязательно) Для авторизованных вызовов добавьте `Authorization: Bearer <ВАШ_ТОКЕН>`.
4. На вкладке **Body** выберите тип `raw` и формат `JSON`. Структура тела:
   ```json
   {
     "query": "...GraphQL-запрос...",
     "variables": {
       "ключ": "значение"
     }
   }
   ```

## Получение токена
Для большинства публичных запросов авторизация не требуется. Если нужно обращаться к приватным данным (например, списку пользователя), используйте OAuth 2.0 Authorization Code Flow:
1. На https://anilist.co/settings/developer создайте приложение и получите `Client ID`/`Client Secret`.
2. Направьте браузер пользователя на `https://anilist.co/api/v2/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&redirect_uri=<REDIRECT_URI>`.
3. После подтверждения AniList перенаправит на `redirect_uri` c параметром `code`.
4. Обменивайте код на токен через `POST https://anilist.co/api/v2/oauth/token`:
   ```json
   {
     "grant_type": "authorization_code",
     "client_id": "<CLIENT_ID>",
     "client_secret": "<CLIENT_SECRET>",
     "redirect_uri": "<REDIRECT_URI>",
     "code": "<AUTHORIZATION_CODE>"
   }
   ```

Полученный `access_token` передавайте в заголовке `Authorization: Bearer <TOKEN>`.

## Пример: поиск тайтла по названию
```graphql
query ($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    description(asHtml: false)
    genres
    averageScore
    episodes
    siteUrl
  }
}
```
Тело запроса:
```json
{
  "query": "query ($search: String) { Media(search: $search, type: ANIME) { id title { romaji english native } description(asHtml: false) genres averageScore episodes siteUrl } }",
  "variables": {
    "search": "Cowboy Bebop"
  }
}
```

## Пример: персонаж по имени
```graphql
query ($search: String) {
  Character(search: $search) {
    id
    name {
      full
      native
    }
    description
    image {
      large
    }
    siteUrl
  }
}
```

## Пагинация списков
AniList использует объект `Page` для постраничных запросов.
```graphql
query ($page: Int = 1, $perPage: Int = 10, $genre: String) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(genre: $genre, type: ANIME) {
      id
      title {
        romaji
      }
      siteUrl
    }
  }
}
```
Тело запроса для Postman:
```json
{
  "query": "query ($page: Int = 1, $perPage: Int = 10, $genre: String) { Page(page: $page, perPage: $perPage) { pageInfo { total currentPage lastPage hasNextPage } media(genre: $genre, type: ANIME) { id title { romaji } siteUrl } } }",
  "variables": {
    "page": 1,
    "perPage": 5,
    "genre": "Sci-Fi"
  }
}
```

## Пример: топ онгоингов (текущих релизов)
Чтобы получить популярные тайтлы, которые всё ещё выходят, фильтруйте по `status: RELEASING` и отсортируйте по убыванию популярности или рейтинга.

```graphql
query (
  $page: Int = 1,
  $perPage: Int = 10,
  $sort: [MediaSort!] = [POPULARITY_DESC]
) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      hasNextPage
    }
    media(type: ANIME, status: RELEASING, sort: $sort) {
      id
      title {
        romaji
        english
      }
      averageScore
      popularity
      nextAiringEpisode {
        episode
        timeUntilAiring
      }
      siteUrl
    }
  }
}
```

Тело запроса в Postman (пример для топ-5 по популярности):
```json
{
  "query": "query ($page: Int = 1, $perPage: Int = 10, $sort: [MediaSort!] = [POPULARITY_DESC]) { Page(page: $page, perPage: $perPage) { pageInfo { total currentPage hasNextPage } media(type: ANIME, status: RELEASING, sort: $sort) { id title { romaji english } averageScore popularity nextAiringEpisode { episode timeUntilAiring } siteUrl } } }",
  "variables": {
    "page": 1,
    "perPage": 5,
    "sort": ["POPULARITY_DESC"]
  }
}
```

Можно менять `sort` на `TRENDING_DESC`, `SCORE_DESC` или комбинировать несколько критериев (например, `[TRENDING_DESC, POPULARITY_DESC]`), чтобы получить другой порядок выдачи.

## Полезные ссылки
- Документация AniList GraphQL: https://anilist.gitbook.io/anilist-apiv2-docs/
- GraphiQL-песочница AniList: https://anilist.co/graphiql
- Список схемы (SDL): https://github.com/AniList/ApiV2-GraphQL-Docs

