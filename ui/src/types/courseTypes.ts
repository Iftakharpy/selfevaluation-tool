// Corresponds to backend's CourseOut / CourseBase
export interface Course {
  id: string;
  name: string;
  code: string;
  description?: string | null;
}

// Corresponds to backend's CourseCreate
export interface CourseCreate {
  name: string;
  code: string;
  description?: string | null;
}

// Corresponds to backend's CourseUpdate
export interface CourseUpdate {
  name?: string;
  code?: string;
  description?: string | null;
}
