# IBM Chat - Enhanced Features Changelog

## 🎉 Major Updates

### ✅ Authentication System
- **Login/Register Screen**: Users must authenticate before accessing the chat
- **Secure Password Hashing**: SHA-256 encryption for password storage
- **User Management**: Stores user data in `data/usuarios.json`
- **Session Management**: Maintains authenticated state throughout the session
- **Validation**: Username (min 3 chars) and password (min 4 chars) validation

### 🎨 UI/UX Improvements
- **Fixed Gray Rectangle**: Removed the gray rectangle issue on the left sidebar by properly setting the sidebar background color to `COLOR_BARRA_LATERAL_CHAT`
- **Consistent Styling**: All sidebar components now have proper background colors
- **Better Visual Hierarchy**: Clear separation between sections with dividers

### 📎 File Attachment Feature
- **File Picker Dialog**: Click the attachment icon to select files
- **File Upload**: Supports single file selection
- **Visual Feedback**: Shows file name in chat with 📎 emoji
- **Success Notifications**: Confirms when file is attached

### 😊 Emoji Picker
- **20 Popular Emojis**: Quick access to commonly used emojis
- **Grid Layout**: Clean 5-column grid display
- **Click to Insert**: Emojis are inserted at cursor position
- **Dialog Interface**: Modal dialog for emoji selection

### 🎬 GIF Picker
- **GIF Selection**: Choose from popular GIFs
- **URL Support**: Integrates with Giphy URLs
- **Easy Insertion**: One-click GIF sending
- **Visual Indicators**: Shows GIF with 🎬 emoji in chat

### ⚙️ Settings Dialog
- **Theme Selection**: Choose between Dark, Light, or Auto themes
- **Notification Toggle**: Enable/disable notifications
- **Sound Toggle**: Control sound effects
- **Watson AI Configuration**: Edit API Key and Project ID directly
- **Save Functionality**: Persist settings changes

### 🔍 Search Functionality
- **Room Search**: Filter rooms in sidebar by name
- **Message Search**: Search through chat messages
- **Real-time Filtering**: Instant results as you type
- **Search Dialog**: Dedicated search interface for messages
- **Result Display**: Shows found messages with context

## 🛠️ Technical Improvements

### Code Architecture
- **AuthManager Class**: Centralized authentication logic
- **LoginView Component**: Reusable login/register UI
- **Modular Design**: Separated concerns for better maintainability
- **Type Hints**: Improved code documentation with Python type hints

### State Management
- **Authentication State**: Tracks user login status
- **Session Persistence**: Maintains user session
- **Component References**: Proper initialization of UI components

### Error Handling
- **Validation Messages**: Clear error feedback for users
- **Try-Catch Blocks**: Graceful error handling
- **User Notifications**: Informative error messages

## 📋 Feature Details

### Login/Register Flow
1. App starts with login screen
2. User can toggle between login and register modes
3. Form validation ensures data quality
4. Successful authentication loads main chat interface
5. Welcome notification greets the user

### File Attachment Flow
1. Click attachment icon in toolbar
2. System file picker opens
3. Select file (single file supported)
4. File name appears in chat
5. Success notification confirms upload

### Emoji Picker Flow
1. Click emoji icon in toolbar
2. Grid of 20 emojis appears
3. Click desired emoji
4. Emoji inserted into message input
5. Dialog closes automatically

### GIF Picker Flow
1. Click GIF icon in toolbar
2. List of popular GIFs shown
3. Select GIF by clicking button
4. GIF URL sent to chat
5. Success notification appears

### Settings Flow
1. Click settings button in sidebar
2. Settings dialog opens
3. Modify preferences (theme, notifications, etc.)
4. Edit Watson AI credentials
5. Click save to persist changes

### Search Flow
1. **Room Search**: Type in sidebar search bar to filter rooms
2. **Message Search**: Click search icon in header
3. Enter search term in dialog
4. Press Enter to search
5. Results displayed in notification

## 🎯 Key Benefits

1. **Security**: User authentication protects chat access
2. **Usability**: Intuitive UI with clear visual feedback
3. **Functionality**: All toolbar buttons now work
4. **Customization**: Settings allow personalization
5. **Search**: Easy to find rooms and messages
6. **Rich Content**: Support for files, emojis, and GIFs

## 🚀 How to Use

### First Time Setup
1. Run the app: `python flet_app.py`
2. Click "¿No tienes cuenta? Regístrate"
3. Enter username (min 3 chars) and password (min 4 chars)
4. Click "Registrarse"
5. You'll be automatically logged in

### Daily Usage
1. Run the app
2. Enter your credentials
3. Click "Iniciar Sesión"
4. Start chatting!

### Using Features
- **Send Message**: Type and press Ctrl+Enter or click send button
- **Attach File**: Click 📎 icon, select file
- **Add Emoji**: Click 😊 icon, select emoji
- **Send GIF**: Click GIF icon, choose GIF
- **Search Rooms**: Type in sidebar search bar
- **Search Messages**: Click 🔍 icon in header
- **Change Settings**: Click ⚙️ icon in sidebar
- **Pin Message**: Hover over message, click pin icon
- **Logout**: Click "Salir" button in sidebar

## 📝 Notes

- User data stored in `data/usuarios.json`
- Passwords are hashed with SHA-256
- Original file backed up as `flet_app_backup.py`
- All features work offline (except Watson AI summarization)
- Watson AI features require API credentials in `.env`

## 🔧 Configuration

Edit `.env` file for Watson AI integration:
```
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

## 🎨 Design Consistency

All components follow IBM design guidelines:
- Material Design 3 principles
- Consistent color scheme from `design_constants.py`
- Proper spacing and padding
- Smooth animations and transitions
- Accessible UI elements

---

**Made with ❤️ by Bob - Your AI Development Assistant**
