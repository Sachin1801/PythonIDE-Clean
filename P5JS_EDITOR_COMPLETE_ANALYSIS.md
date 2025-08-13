# p5.js Web Editor - Complete Technical Analysis

## Project Overview

The p5.js Web Editor is a browser-based integrated development environment (IDE) designed specifically for creative coding with the p5.js library. It provides a complete coding environment without requiring any local installation, making programming accessible to artists, designers, educators, and beginners.

## Architecture

### Tech Stack

#### Frontend
- **Framework**: React 16.14.0 with Redux for state management
- **Build Tool**: Webpack 5.94.0 with Babel 7 for transpilation
- **Code Editor**: CodeMirror 5.62.0 with custom configurations
- **Styling**: Styled Components 5.3.0 with SCSS for component styles
- **UI Components**: 
  - react-split-pane for resizable panels
  - react-router for navigation
  - react-final-form for form handling

#### Backend
- **Runtime**: Node.js with Express 4.18.2
- **Database**: MongoDB with Mongoose 8.16.3
- **Session Management**: express-session with connect-mongo
- **Authentication**: Passport.js with local, GitHub, and Google OAuth strategies

#### Development Tools
- **Type Checking**: TypeScript 5.8.3 (partial implementation)
- **Testing**: Jest 29.7.0 with React Testing Library
- **Linting**: ESLint with Airbnb config
- **Storybook**: Version 7.6.8 for component development

## Core Features

### 1. Code Editing System

#### Editor Configuration (`/client/modules/IDE/components/Editor/index.jsx`)
The editor implements CodeMirror with extensive customizations:

```javascript
// Key configurations at lines 122-168
{
  theme: 'p5-light' | 'p5-dark' | 'p5-contrast',
  lineNumbers: true,
  styleActiveLine: true,
  inputStyle: 'contenteditable',
  lineWrapping: false,
  fixedGutter: false,
  foldGutter: true,
  gutters: ['CodeMirror-foldgutter', 'CodeMirror-lint-markers'],
  keyMap: 'sublime',
  lint: {
    onUpdateLinting: (annotations) => {...},
    options: {
      asi: true,
      eqeqeq: false,
      '-W041': false,
      esversion: 11
    }
  }
}
```

#### Language Support
- **JavaScript**: Custom p5.js mode with syntax highlighting (`/client/utils/p5-javascript.js`)
- **HTML**: HTMLMixed mode with embedded CSS/JS support
- **CSS**: Standard CSS mode with linting via CSSLint
- **JSON**: JSON mode with validation
- **GLSL**: Shader support (.vert, .frag files)
- **Markdown**: Basic markdown support

#### Linting Integration
- **JSHint**: JavaScript validation with p5.js globals
- **CSSLint**: CSS validation
- **HTMLHint**: HTML validation
- Real-time error markers in gutters
- Accessibility announcements for screen readers

### 2. Code Execution System

#### Preview Architecture (`/client/modules/IDE/components/PreviewFrame.jsx`)
Code runs in a sandboxed iframe with specific security attributes:

```javascript
// Sandbox configuration at lines 25-28
sandbox="allow-forms allow-modals allow-pointer-lock allow-popups 
         allow-same-origin allow-scripts allow-top-navigation-by-user-activation 
         allow-downloads"

allow="accelerometer; ambient-light-sensor; autoplay; bluetooth; camera; 
       encrypted-media; geolocation; gyroscope; hid; microphone; magnetometer; 
       midi; payment; usb; serial; vr; xr-spatial-tracking"
```

#### Execution Pipeline (`/client/modules/Preview/EmbedFrame.jsx`)

1. **File Compilation** (lines 196-353)
   - Combines HTML, CSS, and JavaScript files
   - Resolves file dependencies
   - Injects required libraries

2. **JavaScript Preprocessing** (`jsPreprocess` function, lines 134-165)
   - Comment removal using decomment library
   - Loop protection injection via loop-protect
   - Syntax validation with JSHint
   - Source mapping for error tracking

3. **HTML Generation** (lines 354-436)
   - Creates complete HTML document
   - Injects scripts in correct order
   - Adds console hijacking code
   - Includes error handling

#### Message Communication (`/client/utils/dispatcher.js`)
Bidirectional communication between editor and preview:

```javascript
// Message types
{
  START: 'START',      // Begin execution
  STOP: 'STOP',        // Stop execution
  REGISTER: 'REGISTER', // Register frame
  FILES: 'FILES',      // Update files
  SKETCH: 'SKETCH',    // Load sketch
  EXECUTE: 'EXECUTE'   // Run console command
}
```

### 3. Console Implementation

#### Console Component (`/client/modules/IDE/components/Console.jsx`)
- Uses console-feed library for log rendering
- Captures all console methods (log, error, warn, info)
- Supports object inspection and expansion
- Handles async console messages

#### Console Input (`/client/modules/IDE/components/ConsoleInput.jsx`)
- CodeMirror-based input with JavaScript syntax
- Command history with arrow key navigation
- Expression evaluation in iframe context
- Autocomplete support

#### Error Handling
- Stack trace parsing with source mapping
- Line number correlation to original files
- Infinite loop detection and recovery
- Runtime error capture and display

### 4. File Management System

#### File Structure
```javascript
// Redux state shape for files
{
  id: 'root',
  name: 'root',
  children: [
    {
      id: 'file-id',
      name: 'sketch.js',
      content: '// code here',
      fileType: 'file',
      url: null  // or S3 URL for uploaded files
    }
  ],
  fileType: 'folder'
}
```

#### File Operations
- Create, rename, delete files and folders
- Upload files (images, sounds, data)
- Download individual files or entire project as ZIP
- File type detection and appropriate syntax highlighting

### 5. Project Management

#### Project Structure (`/server/models/project.js`)
```javascript
{
  name: String,
  user: ObjectId,
  serveSecure: Boolean,
  files: [FileSchema],
  slug: String,  // URL-friendly name
  createdAt: Date,
  updatedAt: Date
}
```

#### Project Operations
- Auto-save with debouncing (1 second delay)
- Manual save with Cmd/Ctrl+S
- Fork/duplicate projects
- Share via unique URLs
- Download as ZIP archive

### 6. User System

#### Authentication Methods
1. **Local Authentication**: Email/password with bcrypt
2. **GitHub OAuth**: Via passport-github2
3. **Google OAuth**: Via passport-google-oauth20

#### User Roles and Permissions
- Regular users: Create, edit own projects
- Verified users: Additional storage quota
- Example users: Special accounts for p5.js examples

### 7. Asset Management

#### Storage System
- **AWS S3 Integration**: For file uploads
- **Size Limits**: Configurable via UPLOAD_LIMIT (default 250MB)
- **File Types**: Images, sounds, JSON, CSV, text files
- **CDN Support**: Optional S3_BUCKET_URL_BASE for CDN

#### Asset Handling
- Direct upload to S3 with pre-signed URLs
- Automatic URL resolution in code
- Thumbnail generation for images
- CORS configuration for cross-origin access

### 8. Preview Server

#### Separate Server (`/server/previewServer.js`)
- Runs on different port (default 8002)
- Handles iframe content delivery
- Serves compiled sketches
- Manages asset delivery

#### Security Features
- CORS configuration for allowed origins
- Content Security Policy headers
- Sandboxed execution environment
- XSS prevention measures

### 9. Development Features

#### Hot Module Replacement
- Webpack Dev Server with HMR
- React Refresh for component updates
- Preserves application state during development

#### Code Quality Tools
- ESLint with custom rules
- Prettier for code formatting
- Husky for pre-commit hooks
- TypeScript for gradual typing

### 10. UI/UX Components

#### Layout System
- **Responsive Design**: Mobile, tablet, desktop breakpoints
- **Split Panes**: Resizable editor/preview panels
- **Themes**: Light, dark, high contrast modes
- **Accessibility**: ARIA labels, keyboard navigation

#### Component Library
- Custom styled components
- Icon system with React Icons
- Tooltip system with Primer
- Modal/dialog components
- Dropdown menus
- Tab interfaces

### 11. Internationalization

#### i18n Support (`/translations/`)
- Multiple language support via i18next
- Languages: English, Spanish, Japanese, Korean, Portuguese, etc.
- Lazy loading of translation files
- RTL language support

### 12. Performance Optimizations

#### Code Splitting
- Route-based splitting
- Lazy loading of heavy components
- Dynamic imports for libraries

#### Caching Strategies
- Static asset caching with versioning
- MongoDB connection pooling
- Browser localStorage for preferences

#### Bundle Optimization
- Tree shaking with Webpack
- Minification with Terser
- CSS extraction and optimization

### 13. API Architecture

#### RESTful Endpoints

**Project Endpoints**
```
GET    /api/projects/:id        - Get project
POST   /api/projects            - Create project
PUT    /api/projects/:id        - Update project
DELETE /api/projects/:id        - Delete project
GET    /api/user/:user/projects - List user projects
```

**File Endpoints**
```
POST   /api/upload              - Upload file to S3
GET    /api/projects/:id/files  - Get project files
DELETE /api/projects/:id/files/:fileId - Delete file
```

**User Endpoints**
```
POST   /api/signup              - Register user
POST   /api/login               - Login
GET    /api/user                - Get current user
PUT    /api/user                - Update user
POST   /api/reset-password      - Password reset
```

### 14. Email System

#### Email Service (Nodemailer + Mailgun)
- Account verification emails
- Password reset emails
- MJML templates for responsive emails
- Configurable sender and domain

### 15. Example Projects System

#### Example Management
- Curated p5.js examples
- ML5.js examples integration
- Generative design examples
- Automated import scripts
- Special example user accounts

### 16. Environment Configuration

#### Required Environment Variables
```env
# Core Settings
API_URL=/editor
PORT=8000
PREVIEW_PORT=8002
MONGO_URL=mongodb://localhost:27017/p5js-web-editor
SESSION_SECRET=[secret]

# Storage
AWS_ACCESS_KEY=[key]
AWS_SECRET_KEY=[secret]
AWS_REGION=[region]
S3_BUCKET=[bucket-name]
S3_BUCKET_URL_BASE=[cdn-url]
UPLOAD_LIMIT=250000000

# Authentication
GITHUB_ID=[client-id]
GITHUB_SECRET=[client-secret]
GOOGLE_ID=[client-id]
GOOGLE_SECRET=[client-secret]

# Email
MAILGUN_KEY=[api-key]
MAILGUN_DOMAIN=[domain]
EMAIL_SENDER=[email]
EMAIL_VERIFY_SECRET_TOKEN=[token]

# Features
CORS_ALLOW_LOCALHOST=true
TRANSLATIONS_ENABLED=true
UI_ACCESS_TOKEN_ENABLED=false
```

### 17. Build and Deployment

#### Build Process
```bash
npm run build:client  # Webpack production build
npm run build:server  # Server bundle
npm run build:examples # Examples bundle
```

#### Deployment Targets
- Heroku support with heroku-postbuild
- Docker containerization ready
- Static asset CDN compatibility
- Environment-based configuration

### 18. Testing Infrastructure

#### Test Suites
- Unit tests for utilities
- Component tests with React Testing Library
- API endpoint tests with Jest
- Snapshot testing for UI components

#### Test Configuration
- Separate Jest projects for client/server
- Mock service worker for API mocking
- Custom test setup files
- Coverage reporting

### 19. Accessibility Features

#### Screen Reader Support
- Live regions for announcements
- Proper heading hierarchy
- Skip navigation links
- Form labels and descriptions

#### Keyboard Navigation
- Tab order management
- Keyboard shortcuts for all actions
- Focus indicators
- Escape key handling for modals

### 20. Advanced Editor Features

#### Code Assistance
- p5.js function autocomplete
- Parameter hints
- Documentation tooltips
- Color picker for color values
- Emmet abbreviations for HTML

#### Editor Enhancements
- Code folding
- Multi-cursor editing
- Find and replace
- Bracket matching
- Auto-indentation

## Data Flow Architecture

### Redux State Management
```javascript
// Store structure
{
  user: { /* authentication state */ },
  ide: { /* IDE settings and state */ },
  project: { /* current project */ },
  files: { /* file tree */ },
  editorState: { /* editor configuration */ },
  console: { /* console messages */ },
  preferences: { /* user preferences */ },
  loading: { /* loading states */ },
  errors: { /* error states */ }
}
```

### Action Flow
1. User interaction triggers action
2. Action dispatched to Redux store
3. Reducers update state
4. Components re-render with new state
5. Side effects handled by middleware

## Security Measures

### Input Validation
- Sanitization of user inputs
- XSS prevention in rendered content
- SQL injection prevention (using MongoDB)
- Path traversal protection

### Authentication Security
- Bcrypt password hashing
- JWT token management
- Session security with secrets
- OAuth state validation

### Content Security
- Iframe sandboxing
- CORS policy enforcement
- Rate limiting on API endpoints
- File upload restrictions

## Performance Metrics

### Load Time Optimizations
- Code splitting reduces initial bundle
- Lazy loading of non-critical features
- CDN usage for static assets
- Gzip compression enabled

### Runtime Performance
- Virtual DOM diffing with React
- Debounced auto-save
- Throttled preview updates
- Efficient file tree rendering

## Browser Compatibility

### Supported Browsers
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

### Progressive Enhancement
- Core functionality without JavaScript
- Fallbacks for unsupported features
- Polyfills for older browsers
- Graceful degradation strategy