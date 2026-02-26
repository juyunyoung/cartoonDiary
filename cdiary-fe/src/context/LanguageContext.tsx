import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'ko' | 'en';

interface TranslationDict {
  [key: string]: {
    ko: string;
    en: string;
  };
}

const translations: TranslationDict = {
  // Common
  "ok": { ko: "확인", en: "OK" },
  "cancel": { ko: "취소", en: "Cancel" },
  "save": { ko: "저장", en: "Save" },
  "loading": { ko: "불러오는 중...", en: "Loading..." },

  // HomeScreen
  "app_title": { ko: "만화 일기", en: "Cartoon Diary" },
  "search_diaries": { ko: "일기 검색", en: "Search Diaries" },
  "edit_profile": { ko: "프로필 수정", en: "Edit Profile" },
  "new_diary": { ko: "새 일기", en: "New Diary" },
  "search_placeholder": { ko: "일기 내용 검색...", en: "Search diaries..." },
  "search_no_results": { ko: "검색 결과가 없습니다.", en: "No search results." },
  "search_try_other": { ko: "다른 키워드로 검색해 보세요.", en: "Try other keywords." },
  "no_diaries": { ko: "등록된 일기가 없습니다.", en: "No diaries yet." },
  "create_first_char": { ko: "첫번째로 당신의 캐릭터를 만드세요", en: "Create your first character" },
  "loading_diaries": { ko: "일기를 불러오는 중...", en: "Loading diaries..." },
  "delete_confirm": { ko: "정말로 이 일기를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.", en: "Are you sure you want to delete this diary? This cannot be undone." },
  "delete_failed": { ko: "일기 삭제에 실패했습니다.", en: "Failed to delete diary." },

  // UserProfileScreen
  "profile_title": { ko: "사용자 프로필", en: "User Profile" },
  "username": { ko: "사용자 이름", en: "Username" },
  "email": { ko: "이메일", en: "Email" },
  "logout": { ko: "로그아웃", en: "Log Out" },
  "withdraw": { ko: "계정 탈퇴", en: "Withdraw (Delete Account)" },
  "withdraw_confirm": { ko: "정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.", en: "Are you sure you want to delete your account? This cannot be undone." },
  "withdraw_failed": { ko: "계정 삭제에 실패했습니다.", en: "Failed to delete account." },
  "update_failed": { ko: "프로필 수정에 실패했습니다.", en: "Failed to update profile." },
  "regen_image": { ko: "이미지 새로 고치기 (재생성)", en: "Refresh Image (Regenerate)" },
  "regen_failed": { ko: "캐릭터 재생성에 실패했습니다.", en: "Failed to regenerate character." },
  "change_char_settings": { ko: "캐릭터 설정(성별, 머리 등) 변경하기", en: "Change character settings (gender, hair, etc.)" },

  // CharacterCreationScreen
  "create_char_title": { ko: "캐릭터 생성", en: "Create Character" },
  "gender": { ko: "성별", en: "Gender" },
  "female": { ko: "여성", en: "Female" },
  "male": { ko: "남성", en: "Male" },
  "hair_style": { ko: "머리 스타일", en: "Hair Style" },
  "hair_long": { ko: "긴 머리", en: "Long Hair" },
  "hair_medium": { ko: "짧은 머리", en: "Medium Hair" },
  "hair_short": { ko: "쇼컷", en: "Short Hair" },
  "others": { ko: "기타", en: "Others" },
  "glasses": { ko: "안경", en: "Glasses" },
  "freckles": { ko: "주근깨", en: "Freckles" },
  "generate_char": { ko: "캐릭터 만들기", en: "Create Character" },
  "generating": { ko: "생성 중...", en: "Generating..." },
  "regen": { ko: "다시 생성", en: "Regenerate" },
  "save_char": { ko: "저장하기", en: "Save Character" },
  "char_creation_description": { ko: "당신의 이야기 속 주인공을 설정해주세요.", en: "Please set the protagonist of your story." },
  "char_like_it": { ko: "마음에 드시나요?", en: "Do you like it?" },
  "char_save_or_regen": { ko: "캐릭터를 저장하거나 다시 생성해보세요.", en: "Save the character or try regenerating." },
  "char_gen_failed": { ko: "캐릭터 생성에 실패했습니다. 다시 시도해 주세요.", en: "Failed to generate character. Please try again." },
  "char_save_failed": { ko: "캐릭터 저장에 실패했습니다. 다시 시도해 주세요.", en: "Failed to save character. Please try again." },

  // WriteDiaryScreen
  "how_was_day": { ko: "오늘 하루는 어땠나요?", en: "How was your day?" },
  "write_story": { ko: "오늘의 이야기를 들려주세요", en: "Write your story" },
  "write_placeholder": { ko: "무슨 일이 있었나요?", en: "What happened today?" },
  "chars_count": { ko: "자", en: "chars" },
  "choose_style": { ko: "스타일 선택", en: "Choose a Style" },
  "style_cute": { ko: "귀여운", en: "Cute" },
  "style_comedy": { ko: "코미디", en: "Comedy" },
  "style_drama": { ko: "드라마", en: "Drama" },
  "style_simple": { ko: "심플한", en: "Simple" },
  "style_cute_desc": { ko: "부드럽고 사랑스러운", en: "Soft & Adorable" },
  "style_comedy_desc": { ko: "웃기고 과장된", en: "Funny & Exaggerated" },
  "style_drama_desc": { ko: "진지하고 감성적인", en: "Serious & Emotional" },
  "style_simple_desc": { ko: "깔끔하고 명료한", en: "Clean & Simple" },
  "generate_comic": { ko: "만화 생성하기", en: "Generate Comic" },
  "gen_start_failed": { ko: "일기 생성 시작에 실패했습니다.", en: "Failed to start generation." },

  // ResultScreen
  "your_comic": { ko: "나의 만화", en: "Your Comic" },
  "today_diary": { ko: "오늘의 일기", en: "Today's Diary" },
  "regenerate": { ko: "재생성", en: "Regenerate" },
  "save_share": { ko: "저장 및 공유", en: "Save & Share" },
  "saved_at": { ko: "저장되었습니다!", en: "Saved!" },
  "regen_start_failed": { ko: "재생성 시작에 실패했습니다.", en: "Failed to start regeneration." },

  // Auth
  "sign_in_title": { ko: "로그인", en: "Sign In" },
  "sign_up_title": { ko: "회원가입", en: "Sign Up" },
  "welcome": { ko: "환영합니다!", en: "Welcome!" },
  "welcome_back": { ko: "다시 오신 것을 환영합니다", en: "Welcome Back" },
  "create_account": { ko: "계정 만들기", en: "Create Account" },
  "password": { ko: "비밀번호", en: "Password" },
  "confirm_password": { ko: "비밀번호 확인", en: "Confirm Password" },
  "password_mismatch": { ko: "비밀번호가 일치하지 않습니다.", en: "Passwords do not match" },
  "already_have_account": { ko: "이미 계정이 있으신가요?", en: "Already have an account?" },
  "no_account": { ko: "계정이 없으신가요?", en: "Don't have an account?" },
  "register_success": { ko: "회원가입이 완료되었습니다! 환영합니다.", en: "Registration successful! Welcome." },
  "registration_failed": { ko: "회원가입에 실패했습니다.", en: "Registration failed." },
  "invalid_auth": { ko: "아이디 또는 비밀번호가 잘못되었습니다.", en: "Invalid username or password." },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(
    (localStorage.getItem('language') as Language) || 'ko'
  );

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string): string => {
    const entry = translations[key];
    if (!entry) {
      console.warn(`Translation key not found: ${key}`);
      return key;
    }
    return entry[language];
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
