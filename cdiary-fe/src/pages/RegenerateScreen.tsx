import React from 'react';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';

export const RegenerateScreen: React.FC = () => {
  return (
    <AppShell>
      <TopBar title="Regenerate" showBack />
      <div>Regenerate Screen Placeholder</div>
    </AppShell>
  );
};
