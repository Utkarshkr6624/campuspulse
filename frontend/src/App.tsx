import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './components/RequireAuth.tsx'
import { AuthProvider } from './hooks/useAuth.tsx'
import { AppLayout } from './layouts/AppLayout.tsx'
import { AnalyticsPage } from './pages/AnalyticsPage.tsx'
import { AssignmentsPage } from './pages/AssignmentsPage.tsx'
import { AttendancePage } from './pages/AttendancePage.tsx'
import { CoursesPage } from './pages/CoursesPage.tsx'
import { EnrollmentsPage } from './pages/EnrollmentsPage.tsx'
import { ExamsPage } from './pages/ExamsPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'
import { MarksPage } from './pages/MarksPage.tsx'
import { NotFoundPage } from './pages/NotFoundPage.tsx'
import { OverviewPage } from './pages/OverviewPage.tsx'
import { PlannerPage } from './pages/PlannerPage.tsx'
import { RegisterPage } from './pages/RegisterPage.tsx'
import { StudentsPage } from './pages/StudentsPage.tsx'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<RequireAuth />}>
            <Route element={<AppLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="marks" element={<MarksPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="exams" element={<ExamsPage />} />
              <Route path="assignments" element={<AssignmentsPage />} />
              <Route path="planner" element={<PlannerPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="enrollments" element={<EnrollmentsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
