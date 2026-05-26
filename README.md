# HomeShip

Imagine your apartment is your spaceship and you are the crew on this ship! You have lots of maintenance tasks you need to keep track of: laundry, watering plants, vacuum cleaning, and you need to make sure you have enough supplies. With the HomeShip App, all members of your household are crew members with the access to the ship console, you can create tasks, shopping lists and share all of it with each other. As long, as you keep your cargo bay full, and complete all maintenance tasks, you make progress through your journey in space and gain light years of travel. But be careful, procrastinating on maintenance will result in yellow or even red alert and endanger your ship! Avoid auto-destruction and try to get as far away from Earth as possible! Each day without red alert on your HomeShip will add another light year to your journey through the galaxy.

---

## Overview

**Problem.** Keeping track of household chores is tedious but necessary. With several people living together, this task can become even more complicated.

**Solution.** Sharing a household chores list with everyone allows keeping track of what needs to be done, and what was already done by someone else. The space travel angle makes tedious tasks more fun.

### Key Features
- JWT-based authentication
- CRUD operations for HomeShip, User, Task, Supply
- Automatic computation of distance traveled by a HomeShip

## Database Schema

### `users`
| Column        | Type    | Notes                            |
|---------------|---------|----------------------------------|
| user_id       | UUID    | primary key                      |
| username      | VARCHAR | unique, not null                 |
| email         | VARCHAR | unique, not null                 |
| password_hash | VARCHAR | not null, bcrypt hash            |

### `ships`
| Column     | Type    | Notes                  |
|------------|---------|------------------------|
| ship_id    | UUID    | primary key            |
| shipname   | VARCHAR | not null               |
| start_date | DATE    | not null               |

Calculated properties (not stored):

* alert state — derived from related tasks and supplies
* distance traveled — derived from `start_date` and alert history

### `ship_members`
Join table linking users to ships (many-to-many) with role data.

| Column  | Type    | Notes                                                |
|---------|---------|------------------------------------------------------|
| user_id | UUID    | composite PK, references `users.user_id`             |
| ship_id | UUID    | composite PK, references `ships.ship_id`             |
| role    | VARCHAR | not null, default `"Crew Member"`                    |

### `tasks`
| Column      | Type        | Notes                                              |
|-------------|-------------|----------------------------------------------------|
| task_id     | UUID        | primary key                                        |
| ship_id     | UUID        | not null, references `ships.ship_id`               |
| frequency   | INTERVAL    | null for non-repeating tasks                       |
| content     | VARCHAR     | not null                                           |
| date_last   | DATE        | null if never completed                            |
| date_due    | DATE        | null for archived non-repeating tasks              |
| alert_state | ALERT_STATE | not null, default `green` (see enum below)         |

### `supplies`
| Column      | Type        | Notes                                              |
|-------------|-------------|----------------------------------------------------|
| supply_id   | UUID        | primary key                                        |
| ship_id     | UUID        | not null, references `ships.ship_id`               |
| name        | VARCHAR     | not null                                           |
| in_stock    | BOOLEAN     | not null                                           |
| quantity    | INTEGER     | null when tracked only by `in_stock`               |
| alert_state | ALERT_STATE | not null, default `green` (see enum below)         |

### `alert_state` enum
Shared by `tasks` and `supplies`.

| Value           | Task meaning                                  | Supply meaning                          |
|-----------------|-----------------------------------------------|-----------------------------------------|
| `inactive`      | Non-repeating task, completed and archived    | Item no longer tracked                  |
| `green`         | Repeating task completed on time              | In stock                                |
| `yellow`        | Repeating task postponed once                 | Running low                             |
| `red`           | Repeating task postponed twice                | Out of stock                            |
| `auto-destruct` | Task cannot be postponed anymore              | Critical-item outage                    |

---