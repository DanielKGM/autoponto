import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { HelmetProvider } from "react-helmet-async";
import { ScrollToTop } from "../shared/ui/ScrollToTop";
import { ToastProvider } from "../shared/ui/Toast";
import { ThemeProvider } from "../shared/theme/ThemeContext";
import { AdminAcademicoPage, AdminIotPage } from "../features/admin";
import { LessonDetailPage, TurmaAulaPage } from "../features/aulas";
import { NotFoundPage, SignInPage } from "../features/auth";
import { LessonCalendarPage } from "../features/calendario";
import { PublicMapPage } from "../features/mapa";
import { ProfilePage } from "../features/perfil";
import { StudentBiometricsPage, StudentDashboardPage } from "../features/aluno";
import { TeacherDashboardPage } from "../features/professor";
import { ProtectedLayout } from "./ProtectedLayout";
import { RequireArea } from "./RequireArea";
import { RootRedirect } from "./RootRedirect";
import { routerBasename } from "./basename";
import { destinoAposLogin } from "./navigation";

export default function App() {
  return (
    <HelmetProvider>
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter basename={routerBasename}>
            <ScrollToTop />
            <Routes>
              <Route path="/" element={<RootRedirect />} />
              <Route path="/signin" element={<SignInPage resolveDestination={destinoAposLogin} />} />
              <Route path="/mapa-iot" element={<PublicMapPage />} />
              <Route element={<ProtectedLayout />}>
                <Route
                  path="/app/aluno"
                  element={
                    <RequireArea area="aluno">
                      <StudentDashboardPage />
                    </RequireArea>
                  }
                />
                <Route
                  path="/app/aluno/calendario"
                  element={<Navigate to="/app/calendario" replace />}
                />
                <Route
                  path="/app/calendario"
                  element={
                    <RequireArea area="calendario">
                      <LessonCalendarPage />
                    </RequireArea>
                  }
                />
                <Route
                  path="/app/aluno/biometria"
                  element={
                    <RequireArea area="aluno">
                      <StudentBiometricsPage />
                    </RequireArea>
                  }
                />
                <Route path="/app/turmas/:turmaId" element={<TurmaAulaPage />} />
                <Route path="/app/turmas/:turmaId/aulas/:aulaId" element={<TurmaAulaPage />} />
                <Route path="/app/aulas/:aulaId" element={<LessonDetailPage />} />
                <Route path="/app/mapa-iot" element={<PublicMapPage embedded />} />
                <Route
                  path="/app/professor"
                  element={
                    <RequireArea area="professor">
                      <TeacherDashboardPage />
                    </RequireArea>
                  }
                />
                <Route
                  path="/app/admin"
                  element={
                    <RequireArea area="admin">
                      <Navigate to="/app/admin/academico" replace />
                    </RequireArea>
                  }
                />
                <Route
                  path="/app/admin/academico"
                  element={
                    <RequireArea area="admin">
                      <AdminAcademicoPage />
                    </RequireArea>
                  }
                />
                <Route
                  path="/app/admin/iot"
                  element={
                    <RequireArea area="admin">
                      <AdminIotPage />
                    </RequireArea>
                  }
                />
                <Route path="/app/perfil" element={<ProfilePage />} />
              </Route>
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </HelmetProvider>
  );
}
