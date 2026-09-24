import React, { useEffect, useMemo, useState } from 'react';
import { getReviewPrompts } from '../api/client';
import type { ReviewPromptBundle } from '../types';
import './ReviewPromptPanel.css';

interface ReviewPromptPanelProps {
    researchPlan: string;
    formData: Record<string, unknown>;
    onClose: () => void;
}

type PromptTab = 'agentB' | 'agentA';

const copyText = async (value: string): Promise<void> => {
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
        return;
    }

    const textarea = document.createElement('textarea');
    textarea.value = value;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    const copied = document.execCommand('copy');
    textarea.remove();
    if (!copied) throw new Error('コピーに失敗しました');
};

export const ReviewPromptPanel: React.FC<ReviewPromptPanelProps> = ({
    researchPlan,
    formData,
    onClose,
}) => {
    const [prompts, setPrompts] = useState<ReviewPromptBundle | null>(null);
    const [activeTab, setActiveTab] = useState<PromptTab>('agentB');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        let active = true;
        setLoading(true);
        getReviewPrompts(researchPlan, formData)
            .then((result) => {
                if (active) {
                    setPrompts(result);
                    setError(null);
                }
            })
            .catch((err) => {
                if (active) {
                    setError(err instanceof Error ? err.message : 'プロンプトの取得に失敗しました');
                }
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [researchPlan, formData]);

    const currentPrompt = useMemo(() => {
        if (!prompts) return '';
        return activeTab === 'agentB'
            ? [
                '## System instruction',
                prompts.agentBSystemInstruction,
                '',
                '## Review prompt',
                prompts.agentBPrompt,
            ].join('\n')
            : [
                '## System instruction',
                prompts.agentASystemInstruction,
                '',
                '## Revision prompt template',
                prompts.agentAPromptTemplate,
            ].join('\n');
    }, [activeTab, prompts]);

    const fullPrompt = useMemo(() => {
        if (!prompts) return '';
        return [
            '## Agent B system instruction',
            prompts.agentBSystemInstruction,
            '',
            '## Agent B review prompt',
            prompts.agentBPrompt,
            '',
            '## Agent A system instruction',
            prompts.agentASystemInstruction,
            '',
            '## Agent A revision prompt template',
            prompts.agentAPromptTemplate,
        ].join('\n');
    }, [prompts]);

    const handleCopy = async (value: string) => {
        try {
            await copyText(value);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1800);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'コピーに失敗しました');
        }
    };

    return (
        <div className="review-prompt-panel">
            <div className="modal-header">
                <div>
                    <h2>🧾 マルチエージェントレビュー用プロンプト</h2>
                    <p className="review-prompt-subtitle">
                        実際のAgent B審査とAgent A修正で使うプロンプトを表示しています。外部AIへ貼り付ける場合は、研究情報の扱いに注意してください。
                    </p>
                </div>
                <button className="modal-close" onClick={onClose} aria-label="閉じる">×</button>
            </div>

            {loading && <p className="review-prompt-status">プロンプトを準備しています...</p>}
            {error && <p className="review-prompt-error">{error}</p>}

            {prompts && (
                <>
                    <div className="review-prompt-tabs" role="tablist" aria-label="レビューエージェント">
                        <button
                            className={activeTab === 'agentB' ? 'active' : ''}
                            onClick={() => setActiveTab('agentB')}
                            role="tab"
                            aria-selected={activeTab === 'agentB'}
                        >
                            Agent B：倫理審査
                        </button>
                        <button
                            className={activeTab === 'agentA' ? 'active' : ''}
                            onClick={() => setActiveTab('agentA')}
                            role="tab"
                            aria-selected={activeTab === 'agentA'}
                        >
                            Agent A：修正
                        </button>
                    </div>

                    <div className="review-prompt-description">
                        {activeTab === 'agentB'
                            ? '研究計画と申請書データを審査するプロンプトです。外部AIでレビューする場合はこちらを使います。'
                            : 'Agent Bの指摘を受けて申請書データを修正するプロンプトのテンプレートです。'}
                    </div>

                    <textarea
                        className="review-prompt-textarea"
                        value={currentPrompt}
                        readOnly
                        aria-label="レビュー用プロンプト"
                    />

                    <div className="review-prompt-actions">
                        <button className="action-btn secondary" onClick={() => handleCopy(currentPrompt)}>
                            📋 このプロンプトをコピー
                        </button>
                        <button className="action-btn primary" onClick={() => handleCopy(fullPrompt)}>
                            📋 全プロンプトをコピー
                        </button>
                        {copied && <span className="review-prompt-copied">コピーしました</span>}
                    </div>
                </>
            )}
        </div>
    );
};
