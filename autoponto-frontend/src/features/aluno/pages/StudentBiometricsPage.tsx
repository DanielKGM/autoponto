import { useState, type ChangeEvent, type FormEvent } from "react";
import { apiFetch, detalheErro } from "../../../shared/api";
import { useSession } from "../../../shared/session";
import { Modal } from "../../../shared/ui/Modal";
import { PageMeta } from "../../../shared/ui/PageMeta";
import { Button } from "../../../shared/ui/Button";
import {
  CameraIcon,
  DatabaseIcon,
  EyeIcon,
  HeadphonesIcon,
  HelpIcon,
  InfoIcon,
  SunIcon,
  TrashIcon,
  UploadIcon,
  UserIcon,
} from "../../../shared/ui/icons";
import {
  BIOMETRIC_INSTRUCTIONS,
  BIOMETRIC_MAX_FILE_BYTES,
  BIOMETRIC_MAX_FILES,
  formatBiometricFileSize,
  type BiometricInstructionIcon,
  validateBiometricFiles,
} from "../studentBiometricsUtils";

function instructionIcon(icon: BiometricInstructionIcon) {
  if (icon === "user") return <UserIcon />;
  if (icon === "sun") return <SunIcon />;
  if (icon === "eye") return <EyeIcon />;
  return <HeadphonesIcon />;
}

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

function fileExtension(file: File) {
  const extension = file.name.split(".").pop();
  return extension ? extension.slice(0, 4).toUpperCase() : "IMG";
}

export function StudentBiometricsPage() {
  const { me } = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const canRegister = me.permissoes.pode_cadastrar_biometria_propria;

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files || []);
    const validationError = validateBiometricFiles(selected);
    setSuccess("");

    if (validationError) {
      setFiles([]);
      setError(validationError);
      event.currentTarget.value = "";
      return;
    }

    setFiles(selected);
    setError("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!canRegister) {
      setError("Sua conta não tem permissão para cadastrar biometria própria.");
      return;
    }

    const validationError = validateBiometricFiles(files);
    if (validationError) {
      setError(validationError);
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
      <PageMeta title="Biometria | AutoPonto" description="Cadastro biométrico do aluno." />
      <div className="page-header">
        <div className="page-pretitle">Aluno</div>
        <h1 className="page-title">Cadastro de biometria</h1>
        <p className="page-description">Envie fotos recentes do rosto para ativar o reconhecimento nas chamadas.</p>
      </div>

      <section className="card biometric-guidance-card">
        <div className="card-header">
          <div>
            <div className="card-title">Antes de enviar</div>
            <div className="card-subtitle">Fotos boas reduzem falhas no reconhecimento facial.</div>
          </div>
        </div>
        <div className="card-body">
          <div className="biometric-instruction-grid">
            {BIOMETRIC_INSTRUCTIONS.map((instruction) => (
              <div className="biometric-instruction" key={instruction.title}>
                <div className="instruction-illustration" aria-hidden="true">
                  {instructionIcon(instruction.icon)}
                </div>
                <div>
                  <strong>{instruction.title}</strong>
                  <span>{instruction.text}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Minhas capturas</div>
            <div className="card-subtitle">
              JPEG, PNG ou WebP · até {BIOMETRIC_MAX_FILES} fotos de {formatBiometricFileSize(BIOMETRIC_MAX_FILE_BYTES)}.
            </div>
            <div className="card-subtitle biometric-privacy-note">
              As imagens são processadas para gerar a biometria e não ficam armazenadas.{" "}
              <button type="button" className="inline-link-button" onClick={() => setPrivacyOpen(true)}>
                Saiba mais
              </button>
            </div>
          </div>
        </div>
        <div className="card-body">
          {!canRegister && <div className="alert alert-error">Apenas alunos podem cadastrar a própria biometria.</div>}
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form className="biometric-form" onSubmit={submit}>
            <input
              id="biometric-files"
              className="file-input-hidden"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={handleFiles}
              disabled={!canRegister || loading}
            />
            <label className={`dropzone biometric-dropzone ${!canRegister || loading ? "disabled" : ""}`} htmlFor="biometric-files">
              <CameraIcon />
              <span className="hint">Arraste as fotos aqui ou clique para escolher</span>
              <span className="sub">Use imagens nítidas e recentes. O limite também é validado pela API.</span>
            </label>

            {files.length > 0 && (
              <div className="biometric-upload-list" aria-label="Arquivos selecionados">
                {files.map((file) => (
                  <div className="upload-row biometric-upload-row" key={`${file.name}-${file.size}-${file.lastModified}`}>
                    <div className="icon">{fileExtension(file)}</div>
                    <div>
                      <div className="cell-strong">{file.name}</div>
                      <div className="upload-meta">{formatBiometricFileSize(file.size)} · {file.type}</div>
                    </div>
                    <span className="status status-blue">Pronta</span>
                  </div>
                ))}
              </div>
            )}

            <div className="form-actions">
              <Button type="submit" disabled={!canRegister || loading} className="btn-lg biometric-action-btn">
                <UploadIcon />
                {loading ? "Enviando..." : "Cadastrar biometria"}
              </Button>
              {files.length > 0 && (
                <Button
                  type="button"
                  variant="secondary"
                  className="btn-lg biometric-action-btn"
                  disabled={loading}
                  onClick={() => {
                    setFiles([]);
                    setError("");
                    setSuccess("");
                  }}
                >
                  <TrashIcon />
                  Limpar seleção
                </Button>
              )}
            </div>
          </form>
        </div>
      </section>

      <Modal
        open={privacyOpen}
        title="Biometria, armazenamento e LGPD"
        size="md"
        onClose={() => setPrivacyOpen(false)}
        footer={
          <button type="button" className="btn btn-primary" onClick={() => setPrivacyOpen(false)}>
            Entendi
          </button>
        }
      >
        <div className="privacy-modal-content">
          <div className="privacy-modal-row">
            <HelpIcon />
            <div>
              <strong>Finalidade</strong>
              <p>As imagens são usadas apenas para cadastrar sua biometria e apoiar o controle de frequência acadêmica.</p>
            </div>
          </div>
          <div className="privacy-modal-row">
            <DatabaseIcon />
            <div>
              <strong>Armazenamento</strong>
              <p>As capturas são processadas para gerar o dado biométrico e não permanecem armazenadas como imagens.</p>
            </div>
          </div>
          <div className="privacy-modal-row">
            <InfoIcon />
            <div>
              <strong>Seus direitos</strong>
              <p>Em caso de dúvida, correção ou solicitação de exclusão, procure a administração responsável pelo AutoPonto.</p>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
