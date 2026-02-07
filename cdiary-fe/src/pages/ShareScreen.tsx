import React from 'react';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';

export const ShareScreen: React.FC = () => {
  return (
    <AppShell>
      <TopBar title="Share" showBack />
      <div>Share Screen Placeholder</div>
    </AppShell>
  );
};
