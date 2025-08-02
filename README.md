# NFC Reader App

A cross-platform Flutter application that can read NFC tags on both iOS and Android devices.

## Features

- ✅ Read NFC tags on iOS and Android
- ✅ Support for multiple NFC technologies:
  - NDEF (NFC Data Exchange Format)
  - ISO7816 (Smart Cards)
  - ISO15693 (Vicinity Cards)
  - FeliCa (Sony's contactless IC cards)
  - Mifare Classic
  - Mifare Ultralight
- ✅ Parse text and URL records from NDEF tags
- ✅ Scan history tracking
- ✅ Beautiful modern UI with gradient design
- ✅ Real-time NFC availability detection

## Prerequisites

### For Windows Development:
1. **Flutter SDK** - Download from [flutter.dev](https://docs.flutter.dev/get-started/install/windows)
2. **Git** - Download from [git-scm.com](https://git-scm.com/download/win)
3. **Android Studio** - Download from [developer.android.com](https://developer.android.com/studio)
4. **Android Device or Emulator** - For testing Android functionality

### For iOS Development (Mac only):
1. **Xcode** - Download from Mac App Store
2. **iOS Device** - Physical device required (NFC doesn't work in simulator)

## Setup Instructions

### 1. Create Flutter Project
```bash
flutter create nfc_reader_app
cd nfc_reader_app
```

### 2. Replace Files
- Replace `lib/main.dart` with the provided `nfc_reader_app.dart` content
- Replace `pubspec.yaml` with the provided content
- Replace `android/app/src/main/AndroidManifest.xml` with the provided content
- Replace `ios/Runner/Info.plist` with the provided content

### 3. Install Dependencies
```bash
flutter pub get
```

### 4. Platform-Specific Setup

#### Android Setup:
- Ensure your `android/app/build.gradle` has `minSdkVersion: 21` or higher
- The Android manifest already includes necessary NFC permissions

#### iOS Setup:
- Open the project in Xcode: `open ios/Runner.xcworkspace`
- In Xcode, go to your project settings
- Under "Signing & Capabilities", add "Near Field Communication Tag Reading"
- Ensure your Apple Developer account has NFC capabilities enabled

### 5. Run the App

#### For Android:
```bash
flutter run
```

#### For iOS (Mac only):
```bash
flutter run
```
**Note:** iOS requires a physical device - NFC doesn't work in the simulator.

## Usage

1. **Launch the app** - It will automatically check NFC availability
2. **Tap "Start NFC Scan"** - The app will start listening for NFC tags
3. **Hold an NFC tag** near your device's NFC antenna
4. **View the results** - The app will display the tag type and data
5. **Check scan history** - View your recent scans at the bottom

## Supported NFC Tag Types

- **NDEF Tags**: Standard NFC tags with text, URLs, or other data
- **Smart Cards**: Credit cards, access cards, etc.
- **Mifare Cards**: Public transport cards, hotel keys, etc.
- **FeliCa Cards**: Japanese transit cards, etc.

## Troubleshooting

### Common Issues:

1. **"NFC Not Available"**
   - Ensure your device has NFC hardware
   - Check that NFC is enabled in device settings
   - For iOS, ensure you're using a physical device (not simulator)

2. **Permission Denied**
   - Grant NFC permissions when prompted
   - For iOS, ensure NFC capability is added in Xcode

3. **Build Errors**
   - Run `flutter clean` then `flutter pub get`
   - Ensure all dependencies are properly installed

### Device Requirements:

- **Android**: Android 4.4+ with NFC hardware
- **iOS**: iPhone 7+ with iOS 11+ (NFC reading requires iOS 11+)

## Development Notes

- The app uses the `nfc_manager` package for cross-platform NFC functionality
- NFC reading is session-based and requires user interaction
- The app automatically handles different NFC technologies
- Scan history is stored in memory (not persistent)

## License

This project is open source and available under the MIT License. 