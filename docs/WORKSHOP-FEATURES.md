# Workshop Feature Assignments

## How It Works
- Each student gets assigned 1-2 features
- Work on a feature branch, PR into `main`
- Start with single agent (Claude Code), progress to multi-agent orchestration
- Features are designed to be independent — minimal merge conflicts

---

## Round 1: Single Agent (1 student, 1 Claude Code instance)
Each student picks one feature and uses Claude Code to implement it end-to-end.

### Feature 1: Due Dates
**Difficulty:** Easy | **Files:** app.py, index.html
- Add a `due_date` field to todos
- Show due date in the UI
- Highlight overdue items in red
- Sort by due date option

### Feature 2: Priority Levels
**Difficulty:** Easy | **Files:** app.py, index.html
- Add priority field (High, Medium, Low)
- Color-code by priority (red, yellow, green)
- Filter by priority
- Sort by priority option

### Feature 3: Categories/Tags
**Difficulty:** Easy | **Files:** app.py, index.html
- Add a category/tag field to todos
- Filter todos by category
- Show category badges in the UI
- Predefined categories: Work, Personal, Shopping, Health

### Feature 4: Search & Filter
**Difficulty:** Easy | **Files:** app.py, index.html
- Add a search bar that filters todos by title
- Filter by status (all, active, completed)
- Show count of active/completed items
- Clear completed button

### Feature 5: Dark Mode
**Difficulty:** Easy | **Files:** index.html (CSS only)
- Add a dark/light mode toggle
- Save preference in localStorage
- Style all elements for both themes
- Smooth transition between modes

### Feature 6: REST API
**Difficulty:** Medium | **Files:** app.py (new routes)
- GET /api/todos — list all todos (JSON)
- POST /api/todos — create a todo
- PUT /api/todos/<id> — update a todo
- DELETE /api/todos/<id> — delete a todo
- Proper HTTP status codes and error handling

### Feature 7: User Authentication
**Difficulty:** Medium | **Files:** app.py, new templates
- Simple login/register with username + password
- Each user sees only their own todos
- Session-based auth (Flask-Login or session cookies)
- Logout functionality

### Feature 8: Export/Import
**Difficulty:** Medium | **Files:** app.py, index.html
- Export todos as JSON file download
- Export todos as CSV file download
- Import todos from JSON/CSV upload
- Bulk operations (delete all completed, mark all complete)

### Feature 9: Drag & Drop Reorder
**Difficulty:** Medium | **Files:** app.py, index.html (+ JS)
- Drag and drop to reorder todos
- Save sort order to database
- Add a `position` column
- Smooth drag animation

### Feature 10: Notifications & Reminders
**Difficulty:** Medium | **Files:** app.py, index.html (+ JS)
- Browser notification permission request
- Notify when a todo is due soon (within 1 hour)
- Visual countdown for upcoming due dates
- "Due today" section at top of list

---

## Round 2: Multi-Agent (1 student, 2-3 Claude Code terminals)
Students take a more complex feature and split the work across multiple agents working simultaneously.

### Example Orchestration:
- **Agent 1:** Backend (routes, database changes)
- **Agent 2:** Frontend (HTML, CSS, JavaScript)
- **Agent 3:** Tests (unit tests, integration tests)

### Complex Features for Multi-Agent:
- **Activity Log:** Track all changes with timestamps, add an activity feed page, write tests
- **Recurring Todos:** Add recurrence rules, auto-create next occurrence, build schedule UI
- **Collaborative Todos:** Share todos between users, assign todos to others, notification system
- **Dashboard/Analytics:** Chart of completion rates, productivity trends, streaks

---

## Round 3: Fleet Orchestration (1 student, N agents working across features)
Students orchestrate a fleet of agents to tackle multiple tasks simultaneously:

### Exercise: "Ship a Release"
Each student orchestrates 3-5 agents to:
1. **Agent 1:** Fix a bug (pre-planted bug in the codebase)
2. **Agent 2:** Add a small feature (from a backlog)
3. **Agent 3:** Write/update tests for existing code
4. **Agent 4:** Update documentation (README, API docs)
5. **Agent 5:** Review and merge the other agents' PRs

The goal is to coordinate all agents, handle conflicts, and ship a clean release.

---

## Bonus: Integration Exercise
After all features are merged, the team works together to:
1. Resolve any merge conflicts
2. Run the full test suite
3. Build the Docker image
4. Deploy to Azure Web Apps
5. Verify everything works in production

---

## Feature Assignment Matrix

| Student | Round 1 Feature | Round 2 Focus |
|---------|----------------|---------------|
| Student 1 | Due Dates | Activity Log (backend) |
| Student 2 | Priority Levels | Activity Log (frontend) |
| Student 3 | Categories/Tags | Activity Log (tests) |
| Student 4 | Search & Filter | Recurring Todos (backend) |
| Student 5 | Dark Mode | Recurring Todos (frontend) |
| Student 6 | REST API | Recurring Todos (tests) |
| Student 7 | User Auth | Dashboard (backend) |
| Student 8 | Export/Import | Dashboard (frontend) |
| Student 9 | Drag & Drop | Dashboard (tests) |
| Student 10 | Notifications | Code review + integration |
