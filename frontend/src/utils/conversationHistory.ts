/**
 * 대화 히스토리 관리 유틸리티
 * 
 * 사용자의 AI 컨시어지 대화 기록을 로컬스토리지에 저장하고 관리합니다.
 */

export interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  query?: string;
  result?: any;
  error?: boolean;
  retryCount?: number;
}

export interface ConversationSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  lastUpdated: Date;
  messageCount: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  messageCount: number;
  lastUpdated: Date;
  preview: string; // 마지막 메시지 미리보기
}

const STORAGE_KEY = 'ai_concierge_conversations';
const MAX_CONVERSATIONS = 20; // 최대 저장 개수
const MAX_MESSAGES_PER_CONVERSATION = 50; // 대화당 최대 메시지 수

class ConversationHistoryManager {
  
  /**
   * 새로운 대화 세션을 생성합니다
   */
  createNewSession(firstMessage?: ChatMessage): string {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const now = new Date();
    
    const session: ConversationSession = {
      id: sessionId,
      title: this.generateSessionTitle(firstMessage),
      messages: firstMessage ? [firstMessage] : [],
      createdAt: now,
      lastUpdated: now,
      messageCount: firstMessage ? 1 : 0
    };
    
    this.saveSession(session);
    return sessionId;
  }

  /**
   * 세션에 메시지를 추가합니다
   */
  addMessageToSession(sessionId: string, message: ChatMessage): void {
    const session = this.getSession(sessionId);
    if (!session) {
      console.warn(`세션을 찾을 수 없습니다: ${sessionId}`);
      return;
    }

    // 메시지 수 제한 확인
    if (session.messages.length >= MAX_MESSAGES_PER_CONVERSATION) {
      // 오래된 메시지 일부 제거 (첫 번째 환영 메시지 제외)
      const welcomeMessage = session.messages[0];
      const recentMessages = session.messages.slice(-MAX_MESSAGES_PER_CONVERSATION + 10);
      session.messages = [welcomeMessage, ...recentMessages];
    }

    session.messages.push(message);
    session.lastUpdated = new Date();
    session.messageCount = session.messages.length;
    
    // 제목이 기본값이고 사용자 메시지인 경우 제목 업데이트
    if (message.type === 'user' && session.title.startsWith('대화 세션')) {
      session.title = this.generateSessionTitle(message);
    }

    this.saveSession(session);
  }

  /**
   * 세션의 여러 메시지를 일괄 업데이트합니다
   */
  updateSessionMessages(sessionId: string, messages: ChatMessage[]): void {
    const session = this.getSession(sessionId);
    if (!session) {
      console.warn(`세션을 찾을 수 없습니다: ${sessionId}`);
      return;
    }

    session.messages = messages.slice(-MAX_MESSAGES_PER_CONVERSATION); // 제한 적용
    session.lastUpdated = new Date();
    session.messageCount = session.messages.length;

    this.saveSession(session);
  }

  /**
   * 세션을 가져옵니다
   */
  getSession(sessionId: string): ConversationSession | null {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return null;

      const conversations: ConversationSession[] = JSON.parse(stored).map((conv: any) => ({
        ...conv,
        createdAt: new Date(conv.createdAt),
        lastUpdated: new Date(conv.lastUpdated),
        messages: conv.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }));

      return conversations.find(conv => conv.id === sessionId) || null;
    } catch (error) {
      console.error('세션 로드 오류:', error);
      return null;
    }
  }

  /**
   * 모든 대화 세션의 요약 목록을 가져옵니다
   */
  getConversationSummaries(): ConversationSummary[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return [];

      const conversations: ConversationSession[] = JSON.parse(stored).map((conv: any) => ({
        ...conv,
        lastUpdated: new Date(conv.lastUpdated)
      }));

      return conversations
        .sort((a, b) => b.lastUpdated.getTime() - a.lastUpdated.getTime())
        .map(conv => ({
          id: conv.id,
          title: conv.title,
          messageCount: conv.messageCount,
          lastUpdated: conv.lastUpdated,
          preview: this.getLastUserMessage(conv.messages)
        }));
    } catch (error) {
      console.error('대화 목록 로드 오류:', error);
      return [];
    }
  }

  /**
   * 세션을 삭제합니다
   */
  deleteSession(sessionId: string): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return;

      const conversations: ConversationSession[] = JSON.parse(stored);
      const filtered = conversations.filter(conv => conv.id !== sessionId);
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('세션 삭제 오류:', error);
    }
  }

  /**
   * 오래된 대화를 정리합니다
   */
  cleanupOldConversations(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return;

      const conversations: ConversationSession[] = JSON.parse(stored).map((conv: any) => ({
        ...conv,
        lastUpdated: new Date(conv.lastUpdated)
      }));

      // 최근 업데이트 순으로 정렬 후 제한 수만큼 유지
      const sortedConversations = conversations
        .sort((a, b) => b.lastUpdated.getTime() - a.lastUpdated.getTime())
        .slice(0, MAX_CONVERSATIONS);

      localStorage.setItem(STORAGE_KEY, JSON.stringify(sortedConversations));
    } catch (error) {
      console.error('대화 정리 오류:', error);
    }
  }

  /**
   * 모든 대화 기록을 삭제합니다
   */
  clearAllConversations(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('전체 대화 삭제 오류:', error);
    }
  }

  /**
   * 세션을 저장합니다 (내부 사용)
   */
  private saveSession(session: ConversationSession): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      let conversations: ConversationSession[] = stored ? JSON.parse(stored) : [];

      // 기존 세션 업데이트 또는 새 세션 추가
      const existingIndex = conversations.findIndex(conv => conv.id === session.id);
      if (existingIndex >= 0) {
        conversations[existingIndex] = session;
      } else {
        conversations.push(session);
      }

      // 제한 수 초과시 오래된 것 제거
      if (conversations.length > MAX_CONVERSATIONS) {
        conversations = conversations
          .sort((a, b) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime())
          .slice(0, MAX_CONVERSATIONS);
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch (error) {
      console.error('세션 저장 오류:', error);
    }
  }

  /**
   * 세션 제목을 생성합니다
   */
  private generateSessionTitle(message?: ChatMessage): string {
    if (!message || message.type !== 'user') {
      return `대화 세션 ${new Date().toLocaleDateString('ko-KR')}`;
    }

    const content = message.content.trim();
    if (content.length <= 20) {
      return content;
    }

    // 첫 20자 + ... 형태로 줄임
    return content.substring(0, 20) + '...';
  }

  /**
   * 마지막 사용자 메시지를 찾습니다
   */
  private getLastUserMessage(messages: ChatMessage[]): string {
    const userMessages = messages.filter(msg => msg.type === 'user');
    if (userMessages.length === 0) return '새로운 대화';

    const lastMessage = userMessages[userMessages.length - 1];
    return lastMessage.content.length > 50 
      ? lastMessage.content.substring(0, 50) + '...'
      : lastMessage.content;
  }

  /**
   * 스토리지 사용량을 확인합니다
   */
  getStorageInfo(): { used: number; available: number; conversationCount: number } {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const conversationCount = stored ? JSON.parse(stored).length : 0;
      const used = stored ? stored.length : 0;
      const available = 5 * 1024 * 1024 - used; // 5MB 기준

      return { used, available, conversationCount };
    } catch (error) {
      console.error('스토리지 정보 확인 오류:', error);
      return { used: 0, available: 5 * 1024 * 1024, conversationCount: 0 };
    }
  }
}

// 싱글톤 인스턴스 export
export const conversationHistory = new ConversationHistoryManager();

// 타입들도 export
export type { ConversationHistoryManager };