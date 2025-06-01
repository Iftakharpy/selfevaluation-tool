// Corresponds to UserOut from backend
export interface User {
  id: string;
  username: string; // email
  display_name: string;
  role: 'student' | 'teacher';
  photo_url?: string | null;
}

// For login form
export interface UserLoginData {
  username: string; // email
  password: string;
}

// For signup form (corresponds to UserCreate from backend)
export interface UserCreateData extends UserLoginData {
  display_name: string;
  role: 'student' | 'teacher';
  photo_url?: string | null;
}
