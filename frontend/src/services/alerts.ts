import Swal from "sweetalert2";

import "sweetalert2/dist/sweetalert2.min.css";

const palette = {
  confirmButtonColor: "#7b5647",
  cancelButtonColor: "#44474b",
};

export async function confirmAction(
  title: string,
  text: string,
  confirmLabel = "Continuar",
): Promise<boolean> {
  const result = await Swal.fire({
    title,
    text,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: confirmLabel,
    cancelButtonText: "Cancelar",
    reverseButtons: true,
    focusCancel: true,
    ...palette,
  });
  return result.isConfirmed;
}

export function showSuccess(title: string, text?: string): void {
  void Swal.fire({
    title,
    text,
    icon: "success",
    timer: 1800,
    showConfirmButton: false,
    ...palette,
  });
}

export function showError(title: string, text?: string): void {
  void Swal.fire({
    title,
    text,
    icon: "error",
    confirmButtonText: "Fechar",
    ...palette,
  });
}
