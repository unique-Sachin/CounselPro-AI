import { api } from "../api";

export interface CatalogFile {
  uid: string;
  filename: string;
  size: number;
  type: string;
  uploaded_at: string;
  status: "uploaded" | "indexed";
}

export async function uploadCatalogFiles(files: File[]): Promise<CatalogFile[]> {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));
  const res = await api.post("/catalog/upload", formData);
  return res.data.files;
}

export async function indexAllCatalogFiles(): Promise<CatalogFile[]> {
  const res = await api.post("/catalog/index");
  return res.data.files;
}

export async function unindexCatalogFile(id: string): Promise<CatalogFile> {
  const res = await api.post(`/catalog/unindex/${id}`);
  return res.data.file;
}

export async function deleteCatalogFile(id: string): Promise<{ success: boolean }> {
  const res = await api.delete(`/catalog/${id}`);
  return res.data;
}

export async function listCatalogFiles(): Promise<CatalogFile[]> {
  const res = await api.get("/catalog/files");
  return res.data;
}
