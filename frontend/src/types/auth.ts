export type UserRole = "MASTER" | "FUNCIONARIO" | "CLIENTE";
export type UserStatus = "PENDING" | "ACTIVE" | "SUSPENDED" | "INVITED";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  firm_id: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
