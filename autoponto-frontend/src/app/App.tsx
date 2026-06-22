import { BrowserRouter, Route, Routes } from "react-router";
import { HelmetProvider } from "react-helmet-async";
import { ScrollToTop } from "../components/common/ScrollToTop";
import { ThemeProvider } from "../context/ThemeContext";
import { EmptyAreaPage } from "../pages/EmptyAreaPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ProfilePage } from "../pages/ProfilePage";
import { PublicMapPage } from "../pages/PublicMapPage";
import { SignInPage } from "../pages/SignInPage";
import { StudentBiometricsPage } from "../pages/StudentBiometricsPage";
import { ProtectedLayout } from "./ProtectedLayout";
import { RequireArea } from "./RequireArea";
import { RootRedirect } from "./RootRedirect";
import { routerBasename } from "./basename";

export default function App() {
  return (
    <HelmetProvider>
      <ThemeProvider>
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
                    <EmptyAreaPage title="Professor" description="Area do professor preparada para as proximas telas." />
                  </RequireArea>
                }
              />
              <Route
                path="/app/admin"
                element={
                  <RequireArea area="admin">
                    <EmptyAreaPage title="Admin" description="Area administrativa preparada para as proximas telas." />
                  </RequireArea>
                }
              />
              <Route path="/app/perfil" element={<ProfilePage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </HelmetProvider>
  );
}
