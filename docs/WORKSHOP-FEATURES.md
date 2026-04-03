# Workshop Feature Backlog

## Vision
Start with an ugly bare-bones todo app. Evolve it into a lightweight agile project management tool with sprints, backlogs, boards, and team collaboration.

---

## 🎨 UI/UX Improvements (Make It Pretty)

### Tier 1: Basic Styling
1. **Modern CSS Framework** — Add Tailwind CSS or Bootstrap, make it not ugly
2. **Responsive Layout** — Mobile-friendly, proper spacing, max-width container
3. **Color Theme** — Professional color palette, consistent typography
4. **Dark Mode** — Toggle between light/dark themes, persist preference
5. **Loading States** — Spinners, skeleton screens, transition animations

### Tier 2: Rich UI
6. **Card-Based Layout** — Replace the HTML table with styled cards
7. **Modal Dialogs** — Add/edit todos in a modal instead of inline
8. **Toast Notifications** — Success/error popups for actions
9. **Drag & Drop** — Reorder items by dragging
10. **Keyboard Shortcuts** — Quick-add (Ctrl+N), toggle (Space), delete (Del)

### Tier 3: Advanced UI
11. **Kanban Board View** — Columns for Open / In Progress / Done
12. **List vs Board Toggle** — Switch between list view and board view
13. **Sidebar Navigation** — Collapsible sidebar with filters, projects, settings
14. **Dashboard with Charts** — Completion rates, velocity, burndown chart
15. **Custom Themes** — Let users pick accent colors, upload a logo

---

## 📋 Core Todo Features (Enhance the Basics)

16. **Due Dates** — Date picker, overdue highlighting, sort by due date
17. **Priority Levels** — High/Medium/Low with color coding and sorting
18. **Categories/Tags** — Tag todos, filter by tag, color-coded badges
19. **Search & Filter** — Search bar, filter by status/priority/tag, clear filters
20. **Edit In Place** — Click a todo title to edit it inline
21. **Subtasks/Checklists** — Nested tasks under a parent todo
22. **Notes/Description** — Expandable rich text description per todo
23. **Attachments** — Upload files/images to a todo
24. **Recurring Tasks** — Daily/weekly/monthly recurrence rules
25. **Bulk Actions** — Select multiple, bulk delete/complete/move

---

## 🏃 Agile/Project Management Features

### Sprints
26. **Sprint Creation** — Create sprints with name, start date, end date
27. **Sprint Backlog** — Assign todos to a sprint, drag between sprints
28. **Sprint Board** — Kanban board filtered to current sprint
29. **Sprint Review** — Summary of completed/incomplete items when sprint ends
30. **Sprint Velocity** — Track story points completed per sprint over time

### Backlog Management
31. **Product Backlog** — Separate view for unassigned/future items
32. **Backlog Prioritization** — Drag to reorder backlog priority
33. **Story Points** — Assign effort estimates (1, 2, 3, 5, 8, 13)
34. **Backlog Grooming View** — Focus mode for estimating and prioritizing

### Project Structure
35. **Multiple Projects** — Create separate projects, switch between them
36. **Project Settings** — Name, description, team members, default sprint length
37. **Epics** — Group related tasks under an epic with progress tracking
38. **Milestones** — Define milestones with target dates and linked tasks
39. **Roadmap View** — Timeline/Gantt-style view of epics and milestones

---

## 👥 Team & Collaboration

40. **User Authentication** — Register/login, session management
41. **User Profiles** — Avatar, display name, role
42. **Task Assignment** — Assign todos to team members
43. **Comments** — Comment thread on each todo
44. **Activity Feed** — Log of all changes with timestamps and who did what
45. **@Mentions** — Mention teammates in comments, trigger notification
46. **Team Dashboard** — Who's working on what, workload distribution
47. **Role-Based Access** — Admin, member, viewer roles

---

## 🔌 API & Integration

48. **REST API** — Full CRUD JSON API for all resources
49. **API Authentication** — API key or token-based auth
50. **Webhook Support** — Fire webhooks on todo create/update/complete
51. **CSV Export** — Download todos/sprints as CSV
52. **CSV Import** — Upload CSV to bulk-create todos
53. **JSON Export/Import** — Full project backup and restore
54. **API Documentation** — Auto-generated Swagger/OpenAPI docs page

---

## 🧪 Quality & DevOps

55. **Unit Tests** — pytest tests for all routes and database operations
56. **Integration Tests** — End-to-end tests with test client
57. **CI/CD Pipeline** — GitHub Actions: lint, test, build, deploy on push
58. **Code Linting** — Add flake8/ruff, fix all lint warnings
59. **Database Migrations** — Use Alembic for schema versioning
60. **Health Check Endpoint** — /health endpoint for monitoring
61. **Logging** — Structured logging with request IDs
62. **Error Pages** — Custom 404, 500 error pages

---

## 🚀 Deployment & Infrastructure

63. **Docker Compose** — Add Redis for sessions, Postgres for data
64. **Azure Web App Deploy** — Container deployment to Azure
65. **Environment Config** — .env file support, separate dev/prod configs
66. **HTTPS/Security** — CSRF protection, secure headers, input sanitization

---

## Feature Assignment Strategy

### Round 1: Single Agent (Pick 1 feature each)
Give students easy/medium features. They use one Claude Code instance.
Suggested first picks: #1-10 (UI), #16-20 (core features)

### Round 2: Multi-Agent (Pick a feature cluster)
Students open 2-3 Claude Code terminals and split work:
- Agent 1: Backend changes
- Agent 2: Frontend changes  
- Agent 3: Tests

Good clusters:
- Sprint system (#26-30)
- Team collaboration (#40-43)
- API layer (#48-51)

### Round 3: Fleet Orchestration
Each student orchestrates 3-5 agents simultaneously:
- Agent 1: Implement a feature
- Agent 2: Implement a different feature
- Agent 3: Write tests for both
- Agent 4: Update docs/README
- Agent 5: Review and fix issues from other agents

### Finale: Ship It
Whole team collaborates to:
1. Resolve merge conflicts
2. Run full test suite
3. Build Docker image
4. Deploy to Azure
5. Demo the working app
