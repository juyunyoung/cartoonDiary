import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { User, Check, Loader2, RefreshCw, Save } from 'lucide-react';
import { api } from '../api/client';
import { useAlert } from '../context/AlertContext';
import { useLanguage } from '../context/LanguageContext';

export const CharacterCreationScreen: React.FC = () => {
  const navigate = useNavigate();
  const { showAlert } = useAlert();
  const { t } = useLanguage();

  // State for character options
  const [gender, setGender] = useState<'female' | 'male'>('female');
  const [hairLength, setHairLength] = useState<'long' | 'medium' | 'short'>('long');
  const [hasGlasses, setHasGlasses] = useState<boolean>(false);
  const [hasFreckles, setHasFreckles] = useState<boolean>(false);

  // State for image generation
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);


  const constructPrompt = () => {
    const genderTerm = gender === 'female' ? 'girl' : 'boy';
    const hairTerm = hairLength === 'long' ? 'long hair' : hairLength === 'medium' ? 'shoulder-length bob hair' : 'short pixie cut hair';
    const glassesTerm = hasGlasses ? ', wearing glasses' : '';
    const frecklesTerm = hasFreckles ? ', with freckles' : '';

    return `A cute cartoon character, ${genderTerm} with ${hairTerm}${glassesTerm}${frecklesTerm}. Simple, clean lines, flat colors, webtoon style. Single face portrait, close-up, front view, face only. Solo character. NO body, NO full body, NO multiple views, NO character sheet, NO split screen. Neutral background.`;
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGeneratedImage(null);
    try {
      const prompt = constructPrompt();
      const result = await api.generateImage(prompt);
      setGeneratedImage(result.image_data); // Use Base64 data for display

    } catch (error) {
      console.error("Failed to generate character:", error);
      showAlert(t('char_gen_failed'));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirmSave = async () => {
    if (!generatedImage) return;

    try {
      // 1. Generate or retrieve userId (Mocking for now)
      const userId = localStorage.getItem('userId') || `user_${Math.random().toString(36).substring(2, 9)}`;
      localStorage.setItem('userId', userId);

      // 2. Save profile image to S3 via backend
      const { s3_key, image_url } = await api.saveProfileImage(userId, generatedImage, constructPrompt());

      // 3. Save character metadata to LocalStorage (with S3 URL this time)
      const characterData = {
        gender,
        hairLength,
        hasGlasses,
        hasFreckles,
        imageUrl: image_url, // Use the permanent S3 URL
        s3Key: s3_key
      };
      localStorage.setItem('user_character', JSON.stringify(characterData));

      // 4. Navigate
      navigate('/profile');
    } catch (error) {
      console.error("Failed to save profile:", error);
      showAlert(t('char_save_failed'));
    }
  };

  const OptionButton = ({
    label,
    selected,
    onClick
  }: {
    label: string;
    selected: boolean;
    onClick: () => void;
  }) => (
    <button
      onClick={onClick}
      className={`
        px-3 py-3 rounded-lg border text-sm font-medium transition-all w-full
        ${selected
          ? 'bg-primary text-white border-primary ring-2 ring-primary/20'
          : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
        }
      `}
    >
      <div className="flex flex-col items-center justify-center gap-1">
        <span>{label}</span>
        {selected && <Check className="w-4 h-4" />}
      </div>
    </button>
  );

  return (
    <AppShell>
      <TopBar
        title={t('create_char_title')}
        showBack={true}
      />

      <div className="p-4 max-w-md mx-auto w-full flex flex-col gap-6 pb-20">
        <div className="text-center py-6">
          {generatedImage ? (
            <div className="w-48 h-48 mx-auto mb-4 rounded-xl overflow-hidden shadow-lg border-2 border-primary/20 bg-white relative">
              <img src={generatedImage} alt="Generated Character" className="w-full h-full object-cover" />
            </div>
          ) : (
            <div className="w-24 h-24 bg-secondary/20 rounded-full mx-auto flex items-center justify-center mb-4 transition-all">
              {isGenerating ? (
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
              ) : (
                <User className="w-12 h-12 text-primary" />
              )}
            </div>
          )}

          <h2 className="text-xl font-bold text-gray-800 dark:text-white">
            {generatedImage ? t('char_like_it') : t('create_first_char')}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {generatedImage ? t('char_save_or_regen') : t('char_creation_description')}
          </p>
        </div>

        {/* Options (Disable while generating or if image exists? Maybe keep enabled to allow quick changes for regeneration) */}
        {!generatedImage && (
          <>
            {/* Gender Selection */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t('gender')}</label>
              <div className="grid grid-cols-2 gap-3">
                <OptionButton
                  label={t('female')}
                  selected={gender === 'female'}
                  onClick={() => setGender('female')}
                />
                <OptionButton
                  label={t('male')}
                  selected={gender === 'male'}
                  onClick={() => setGender('male')}
                />
              </div>
            </div>

            {/* Hair Length Selection */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t('hair_style')}</label>
              <div className="grid grid-cols-3 gap-2">
                <OptionButton
                  label={t('hair_long')}
                  selected={hairLength === 'long'}
                  onClick={() => setHairLength('long')}
                />
                <OptionButton
                  label={t('hair_medium')}
                  selected={hairLength === 'medium'}
                  onClick={() => setHairLength('medium')}
                />
                <OptionButton
                  label={t('hair_short')}
                  selected={hairLength === 'short'}
                  onClick={() => setHairLength('short')}
                />
              </div>
            </div>

            {/* Other Features Selection (Glasses, Freckles) */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">{t('others')}</label>
              <div className="grid grid-cols-2 gap-3">
                <OptionButton
                  label={t('glasses')}
                  selected={hasGlasses}
                  onClick={() => setHasGlasses(!hasGlasses)}
                />
                <OptionButton
                  label={t('freckles')}
                  selected={hasFreckles}
                  onClick={() => setHasFreckles(!hasFreckles)}
                />
              </div>
            </div>
          </>
        )}

        {/* Actions */}
        <div className="pt-4 flex gap-3">
          {generatedImage ? (
            <>
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="flex-1 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 font-bold py-3 px-4 rounded-xl shadow-sm flex items-center justify-center gap-2"
              >
                <RefreshCw className={`w-5 h-5 ${isGenerating ? 'animate-spin' : ''}`} />
                {t('regen')}
              </button>
              <button
                onClick={handleConfirmSave}
                className="flex-1 bg-primary hover:bg-primary/90 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2"
              >
                <Save className="w-5 h-5" />
                {t('save_char')}
              </button>
            </>
          ) : (
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {t('generating')}
                </>
              ) : (
                t('generate_char')
              )}
            </button>
          )}
        </div>
      </div>
    </AppShell>
  );
};
