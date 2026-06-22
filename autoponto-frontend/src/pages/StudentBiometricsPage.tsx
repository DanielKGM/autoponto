import { useState, type ChangeEvent, type FormEvent } from "react";
import { apiFetch, detalheErro } from "../api";
import { useSession } from "../app/session";
import { PageMeta } from "../components/common/PageMeta";
import { Button } from "../components/ui/Button";

function fileToBase64Payload(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",")[1] : result);
    };
    reader.onerror = () => reject(reader.error || new Error("Falha ao ler arquivo."));
    reader.readAsDataURL(file);
  });
}

export function StudentBiometricsPage() {
  const { me } = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const canRegister = me.permissoes.pode_cadastrar_biometria_propria;

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files || []));
    setError("");
    setSuccess("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!canRegister) {
      setError("Sua conta nao tem permissao para cadastrar biometria propria.");
      return;
    }

    if (files.length === 0) {
      setError("Selecione ao menos uma imagem para cadastrar a biometria.");
      return;
    }

    setLoading(true);
    try {
      const capturas = await Promise.all(files.map(fileToBase64Payload));
      const response = await apiFetch<{ embedding_id: string; status: string }>("/me/biometria/", {
        method: "POST",
        body: JSON.stringify({
          capturas,
          versao_modelo: "sface",
        }),
      });
      setSuccess(`Biometria cadastrada com status ${response.status}.`);
      setFiles([]);
    } catch (err) {
      setError(detalheErro(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageMeta title="Biometria | AutoPonto" description="Cadastro biometrico do aluno." />
      <div className="page-header">
        <div className="page-pretitle">Aluno</div>
        <h1 className="page-title">Cadastro de biometria</h1>
        <p className="page-description">Envie uma ou mais imagens do rosto para cadastrar sua biometria no AutoPonto.</p>
      </div>

      <section className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Minhas capturas</div>
            <div className="card-subtitle">As imagens sao processadas pelo backend para gerar o embedding facial.</div>
          </div>
        </div>
        <div className="card-body">
          {!canRegister && <div className="alert alert-error">Apenas alunos podem cadastrar a propria biometria.</div>}
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form className="biometric-form" onSubmit={submit}>
            <div className="form-group">
              <label className="form-label" htmlFor="biometric-files">
                Imagens do rosto
              </label>
              <input
                id="biometric-files"
                className="form-control"
                type="file"
                accept="image/*"
                multiple
                onChange={handleFiles}
                disabled={!canRegister || loading}
              />
              <p className="form-help">Use imagens nitidas e recentes. O limite final de tamanho e quantidade e validado pela API.</p>
            </div>

            {files.length > 0 && (
              <div className="selected-files">
                {files.map((file) => (
                  <span className="status status-blue" key={`${file.name}-${file.size}`}>
                    {file.name}
                  </span>
                ))}
              </div>
            )}

            <Button type="submit" disabled={!canRegister || loading} className="btn-lg">
              {loading ? "Enviando..." : "Cadastrar biometria"}
            </Button>
          </form>
        </div>
      </section>
    </>
  );
}
