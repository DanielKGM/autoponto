import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { HelmetProvider } from "react-helmet-async";
import { ScrollToTop } from "../components/common/ScrollToTop";
import { ToastProvider } from "../components/common/Toast";
import { ThemeProvider } from "../context/ThemeContext";
import { AdminAcademicoPage } from "../pages/admin/AdminAcademicoPage";
import { AdminIotPage } from "../pages/admin/AdminIotPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ProfilePage } from "../pages/ProfilePage";
import { PublicMapPage } from "../pages/PublicMapPage";
import { SignInPage } from "../pages/SignInPage";
import { StudentBiometricsPage } from "../pages/StudentBiometricsPage";
import { TeacherPage } from "../pages/TeacherPage";
import { ProtectedLayout } from "./ProtectedLayout";
import { RequireArea } from "./RequireArea";
import { RootRedirect } from "./RootRedirect";
import { routerBasename } from "./basename";

export default function App() {
  return (
    <HelmetProvider>
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter basename={routerBasename}>
            <ScrollToTop />
            <Routes>
              <Route path="/" element={<RootRedirect />} />
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/mapa-iot" element={<PublicMapPage />} />
              <Route element={<ProtectedLayout />}>
                <Route
                  path="/app/aluno"
                  element={
                    <RequireArea area="aluno">
                      <StudentBiometricsPage />
                    </RequireArea>
                  }
                />
                <Route path="/app/mapa-iot" element={<PublicMapPage embedded />} />
                <Route
                  path="/app/professor"
                  element={
                    <RequireArea area="professor">
                      <TeacherPage />
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
