# Smart Shower OS (showerOS)

A comprehensive operating system for smart showers that integrates music streaming, mobile control, and automated safety features.

## Features

### 🎵 Audio Streaming
- **Spotify Integration**: Connect to your Spotify account and control playback
- **YouTube Audio**: Stream audio directly from YouTube videos
- **Local Music**: Play music files stored locally
- **Bluetooth Support**: Connect external Bluetooth speakers

### 📱 Mobile Control
- **Remote Control**: Turn shower on/off from your phone
- **Temperature Control**: Adjust water temperature remotely
- **Audio Control**: Change tracks, volume, and audio source from mobile app
- **Timer Settings**: Set shower duration and auto-shutoff

### 🚿 Smart Shower Features
- **Auto Shutoff**: Automatically turns off if door isn't opened within 10 minutes
- **Temperature Monitoring**: Real-time water temperature display
- **Flow Control**: Adjustable water pressure and flow rate
- **Safety Features**: Emergency shutoff and leak detection

### 🔒 Safety & Security
- **Motion Detection**: Detects when someone enters/exits shower
- **Water Leak Detection**: Monitors for potential leaks
- **Emergency Shutoff**: Manual and automatic emergency controls
- **Usage Analytics**: Track water usage and shower duration

## Hardware Requirements

### Core Components
- **Raspberry Pi 4** (or similar SBC)
- **Water Flow Sensors**
- **Temperature Sensors**
- **Solenoid Valves** (for water control)
- **Motion Sensors**
- **Door Sensors**
- **Audio Output System**

### Optional Components
- **Touch Screen Display**
- **LED Strip Lighting**
- **Steam Sensors**
- **Water Quality Sensors**

## Software Architecture

```
showerOS/
├── core/                 # Core system components
│   ├── water_control.py  # Water flow and temperature control
│   ├── audio_manager.py  # Audio streaming and playback
│   ├── safety_monitor.py # Safety and monitoring systems
│   └── mobile_api.py     # Mobile app communication
├── services/             # External service integrations
│   ├── spotify_client.py # Spotify API integration
│   ├── youtube_client.py # YouTube audio extraction
│   └── bluetooth_client.py # Bluetooth audio support
├── web/                  # Web interface
│   ├── dashboard.html    # Main control dashboard
│   ├── mobile_app.html   # Mobile-optimized interface
│   └── api/              # REST API endpoints
├── config/               # Configuration files
│   ├── settings.yaml     # System settings
│   └── credentials.yaml  # API credentials
└── utils/                # Utility functions
    ├── audio_utils.py    # Audio processing utilities
    └── safety_utils.py   # Safety monitoring utilities
```

## Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Audio system (speakers/amplifier)
- Network connectivity

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd showerOS
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure settings**
   ```bash
   cp config/settings.yaml.example config/settings.yaml
   # Edit settings.yaml with your preferences
   ```

4. **Set up API credentials**
   ```bash
   cp config/credentials.yaml.example config/credentials.yaml
   # Add your Spotify, YouTube, and other API credentials
   ```

5. **Run the system**
   ```bash
   python main.py
   ```

## Configuration

### Audio Settings
- Spotify Client ID and Secret
- YouTube API Key
- Bluetooth device pairing
- Audio output configuration

### Water Control Settings
- Flow sensor calibration
- Temperature sensor calibration
- Valve control parameters
- Safety thresholds

### Mobile App Settings
- Network configuration
- Security tokens
- Push notification settings

## Usage

### Starting the Shower
1. Open the mobile app or web dashboard
2. Select your preferred audio source (Spotify, YouTube, etc.)
3. Set desired water temperature
4. Press "Start Shower" button
5. Water will begin flowing and audio will start playing

### Audio Control
- **Spotify**: Browse playlists, search songs, control playback
- **YouTube**: Enter video URL or search for music
- **Local Music**: Browse and play local audio files
- **Volume Control**: Adjust volume from mobile app or voice commands

### Safety Features
- **Auto Shutoff**: System automatically turns off if door isn't opened within 10 minutes
- **Manual Override**: Emergency stop button for immediate shutoff
- **Leak Detection**: Automatic shutoff if water leak is detected
- **Temperature Limits**: Prevents scalding with maximum temperature limits

## API Documentation

### REST Endpoints

#### Water Control
- `POST /api/shower/start` - Start shower
- `POST /api/shower/stop` - Stop shower
- `GET /api/shower/status` - Get current status
- `PUT /api/shower/temperature` - Set temperature

#### Audio Control
- `POST /api/audio/spotify/play` - Play Spotify track
- `POST /api/audio/youtube/play` - Play YouTube audio
- `PUT /api/audio/volume` - Adjust volume
- `POST /api/audio/pause` - Pause audio
- `POST /api/audio/resume` - Resume audio

#### Safety
- `GET /api/safety/status` - Get safety system status
- `POST /api/safety/emergency_stop` - Emergency shutoff
- `GET /api/safety/leak_status` - Check for water leaks

## Development

### Adding New Features
1. Create new module in appropriate directory
2. Add configuration options to `settings.yaml`
3. Update API endpoints if needed
4. Add tests for new functionality
5. Update documentation

### Testing
```bash
python -m pytest tests/
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes and add tests
4. Submit pull request

## Troubleshooting

### Common Issues
- **Audio not playing**: Check audio system connections and volume
- **Water not flowing**: Verify valve connections and power
- **Mobile app not connecting**: Check network configuration and firewall settings
- **Spotify not working**: Verify API credentials and internet connection

### Logs
System logs are stored in `logs/` directory:
- `shower.log` - Main system logs
- `audio.log` - Audio system logs
- `safety.log` - Safety system logs
- `mobile.log` - Mobile app communication logs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration documentation

## Roadmap

### Future Features
- **Voice Control**: Amazon Alexa and Google Assistant integration
- **AI Temperature Learning**: Automatic temperature adjustment based on user preferences
- **Water Usage Analytics**: Detailed usage reports and conservation tips
- **Multi-User Profiles**: Support for multiple household members
- **Advanced Audio Features**: Equalizer, audio effects, and playlist management
- **Smart Home Integration**: Works with HomeKit, SmartThings, and other platforms
